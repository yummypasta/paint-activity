# -*- coding: utf-8 -*-
"""
toolbox.py

Create Oficina Toolbar in Sugar


Copyright 2007, NATE-LSI-EPUSP

Oficina is developed in Brazil at Escola Politécnica of
Universidade de São Paulo. NATE is part of LSI (Integrable
Systems Laboratory) and stands for Learning, Work and Entertainment
Research Group. Visit our web page:
www.lsi.usp.br/nate
Suggestions, bugs and doubts, please email oficina@lsi.usp.br

Oficina is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation version 2 of
the License.

Oficina is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with Oficina; if not, write to the
Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
Boston, MA  02110-1301  USA.
The copy of the GNU General Public License is found in the
COPYING file included in the source distribution.


Authors:

Joyce Alessandra Saul               (joycealess@gmail.com)
Andre Mossinato                     (andremossinato@gmail.com)
Nathalia Sautchuk Patrício          (nathalia.sautchuk@gmail.com)
Pedro Kayatt                        (pekayatt@gmail.com)
Rafael Barbolo Lopes                (barbolo@gmail.com)
Alexandre A. Gonçalves Martinazzo   (alexandremartinazzo@gmail.com)

Colaborators:
Bruno Gola                          (brunogola@gmail.com)

Group Manager:
Irene Karaguilla Ficheman           (irene@lsi.usp.br)

Cientific Coordinator:
Roseli de Deus Lopes                (roseli@lsi.usp.br)

UI Design (OLPC):
Eben Eliason                        (eben@laptop.org)

Project Coordinator (OLPC):
Manusheel Gupta                     (manu@laptop.org)

Project Advisor (OLPC):
Walter Bender                       (walter@laptop.org)

"""

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Pango
import logging

from sugar3.activity.widgets import EditToolbar
from sugar3.graphics.toolcombobox import ToolComboBox
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics.toggletoolbutton import ToggleToolButton
from sugar3.graphics.objectchooser import ObjectChooser
from widgets import ButtonStrokeColor
from sugar3.graphics.colorbutton import ColorToolButton

from sugar3.graphics import style

from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbarbox import ToolbarButton, ToolbarBox
from sugar3.activity.widgets import StopButton

from fontcombobox import FontComboBox


class DrawToolbarBox(ToolbarBox):
    """Create toolbars for the activity"""

    def __init__(self, activity):

        self._activity = activity
        ToolbarBox.__init__(self)
        activity_button = ActivityToolbarButton(self._activity)
        self.toolbar.insert(activity_button, -1)

        self._activity.set_toolbar_box(self)

        edit_toolbar = ToolbarButton()
        edit_toolbar.props.page = DrawEditToolbar(self._activity)
        edit_toolbar.props.icon_name = 'toolbar-edit'
        edit_toolbar.props.label = _('Edit')
        self.toolbar.insert(edit_toolbar, -1)

        self._activity.tool_group = None

        tools_builder = ToolsToolbarBuilder(self.toolbar, self._activity)

        shapes_button = ToolbarButton()
        shapes_button.props.page = ShapesToolbar(self._activity)
        shapes_button.props.icon_name = 'shapes'
        shapes_button.props.label = _('Shapes')
        self.toolbar.insert(shapes_button, -1)

        fonts_button = ToolbarButton()
        fonts_button.props.page = TextToolbar(self._activity)
        fonts_button.props.icon_name = 'format-text-size'
        fonts_button.props.label = _('Fonts')
        self.toolbar.insert(fonts_button, -1)

        image_button = ToolbarButton()
        image_button.props.page = ImageToolbar(self._activity)
        image_button.props.icon_name = 'picture'
        image_button.props.label = _('Image')
        self.toolbar.insert(image_button, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_size_request(0, -1)
        separator.set_expand(True)
        self.toolbar.insert(separator, -1)
        separator.show()

        stop = StopButton(self._activity)
        self.toolbar.insert(stop, -1)

        # TODO: workaround
        # the BrushButton does not starts
        self.brush_button = tools_builder._stroke_color.color_button
        area = self._activity.area
        self.brush_button.set_brush_shape(area.tool['line shape'])
        self.brush_button.set_brush_size(area.tool['line size'])
        self.brush_button.set_stamp_size(area.tool['stamp size'])

        # init the color
        cairo_stroke_color = area.tool['cairo_stroke_color']
        red = cairo_stroke_color[0] * 65535
        green = cairo_stroke_color[1] * 65535
        blue = cairo_stroke_color[2] * 65535

        stroke_color = Gdk.Color(red, green, blue)
        self.brush_button.set_color(stroke_color)


##Make the Edit Toolbar
class DrawEditToolbar(EditToolbar):

    def __init__(self, activity):
        EditToolbar.__init__(self)

        self._activity = activity

        self.undo.set_tooltip(_('Undo'))
        self.redo.set_tooltip(_('Redo'))
        self.copy.set_tooltip(_('Copy'))
        self.paste.set_tooltip(_('Paste'))

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        self.insert(separator, -1)

        self._clear_all = ToolButton('edit-clear')
        self.insert(self._clear_all, -1)
        self._clear_all.set_tooltip(_('Clear'))
        self._clear_all.show()

        self.undo.connect('clicked', self._undo_cb)
        self.redo.connect('clicked', self._redo_cb)

        self.copy.connect('clicked', self._copy_cb)
        self.paste.connect('clicked', self._paste_cb)
        self._clear_all.connect('clicked', self._clear_all_cb)

        self._activity.area.connect('undo', self._on_signal_undo_cb)
        self._activity.area.connect('redo', self._on_signal_redo_cb)
        self._activity.area.connect('select', self._on_signal_select_cb)
        self._activity.area.connect('action-saved',
            self._on_signal_action_saved_cb)

    def _undo_cb(self, widget, data=None):
        self._activity.area.undo()

    def _redo_cb(self, widget, data=None):
        self._activity.area.redo()

    def _copy_cb(self, widget, data=None):
        self._activity.area.copy()

    def _paste_cb(self, widget, data=None):
        self._activity.area.paste(self._activity.area)

    def _on_signal_undo_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    def _on_signal_redo_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    def _on_signal_select_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    def _on_signal_action_saved_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    ##define when a button is active
    def _verify_sensitive_buttons(self):
        self.undo.set_sensitive(self._activity.area.can_undo())
        self.redo.set_sensitive(self._activity.area.can_redo())
        self.copy.set_sensitive(self._activity.area.is_selected())
        #TODO: it is not possible to verify this yet.
        #self.paste.set_sensitive(self._activity.area.can_paste())

    def _clear_all_cb(self, widget, data=None):
        self._activity.area.clear()


class DrawToolButton(RadioToolButton):

    def __init__(self, icon_name, tool_group, tooltip):
        RadioToolButton.__init__(self)
        self.props.icon_name = icon_name
        self.props.group = tool_group
        self.set_active(False)
        self.set_tooltip(tooltip)


class ToolsToolbarBuilder():

    #Tool default definitions
    _TOOL_PENCIL_NAME = 'pencil'
    _TOOL_BRUSH_NAME = 'brush'
    _TOOL_ERASER_NAME = 'eraser'
    _TOOL_BUCKET_NAME = 'bucket'
    _TOOL_PICKER_NAME = 'picker'
    _TOOL_STAMP_NAME = 'stamp'
    _TOOL_MARQUEE_RECT_NAME = 'marquee-rectangular'

    ##The Constructor
    def __init__(self, toolbar, activity):

        self._activity = activity
        self.properties = self._activity.area.tool

        self._stroke_color = ButtonStrokeColor(activity)
        #self._stroke_color.set_icon_name('icon-stroke')
        self._stroke_color.set_title(_('Brush properties'))
        self._stroke_color.connect('notify::color', self._color_button_cb)
        item = Gtk.ToolItem()
        item.add(self._stroke_color)
        toolbar.insert(item, -1)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        toolbar.insert(separator, -1)

        self._tool_brush = DrawToolButton('tool-brush',
            activity.tool_group, _('Brush'))
        activity.tool_group = self._tool_brush
        toolbar.insert(self._tool_brush, -1)

        self._tool_eraser = DrawToolButton('tool-eraser',
            activity.tool_group, _('Eraser'))
        toolbar.insert(self._tool_eraser, -1)

        self._tool_bucket = DrawToolButton('tool-bucket',
            activity.tool_group, _('Bucket'))
        toolbar.insert(self._tool_bucket, -1)

        self._tool_picker = DrawToolButton('tool-picker',
            activity.tool_group, _('Picker'))
        toolbar.insert(self._tool_picker, -1)

        self._tool_stamp = DrawToolButton('tool-stamp',
            activity.tool_group, _('Stamp'))
        toolbar.insert(self._tool_stamp, -1)

        is_selected = self._activity.area.is_selected()
        self._tool_stamp.set_sensitive(is_selected)
        self._activity.area.connect('undo', self._on_signal_undo_cb)
        self._activity.area.connect('redo', self._on_signal_redo_cb)
        self._activity.area.connect('select', self._on_signal_select_cb)
        self._activity.area.connect('action-saved',
            self._on_signal_action_saved_cb)

        self._tool_marquee_rectangular = \
            DrawToolButton('tool-marquee-rectangular',
            activity.tool_group, _('Select Area'))
        toolbar.insert(self._tool_marquee_rectangular, -1)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        toolbar.insert(separator, -1)

        # New connect method
        # Using dictionnaries to control tool's properties
        #self._tool_pencil.connect('clicked', self.set_tool,
        #    self._TOOL_PENCIL_NAME)
        self._tool_brush.connect('clicked', self.set_tool,
            self._TOOL_BRUSH_NAME)
        self._tool_eraser.connect('clicked', self.set_tool,
            self._TOOL_ERASER_NAME)
        self._tool_bucket.connect('clicked', self.set_tool,
            self._TOOL_BUCKET_NAME)
        self._tool_picker.connect('clicked', self.set_tool,
            self._TOOL_PICKER_NAME)
        self._tool_stamp.connect('clicked', self.set_tool,
            self._TOOL_STAMP_NAME)
        self._tool_marquee_rectangular.connect('clicked', self.set_tool,
            self._TOOL_MARQUEE_RECT_NAME)

    def set_tool(self, widget, tool_name):
        """
        Set tool to the Area object. Configures tool's color and size.

            @param self -- Gtk.Toolbar
            @param widget -- The connected widget, if any;
                          necessary in case this method is used in a connect()
            @param tool_name --The name of the selected tool
        """
        if tool_name == 'stamp':
            resized_stamp = self._activity.area.setup_stamp()
            self._stroke_color.color_button.set_resized_stamp(resized_stamp)
        else:
            self._stroke_color.color_button.stop_stamping()
        self._stroke_color.update_stamping()
        self.properties['name'] = tool_name
        self._activity.area.set_tool(self.properties)

    def _color_button_cb(self, widget, pspec):
        logging.error('ToolsToolbarBuilder._color_button_cb')

        new_color = widget.get_color()
        self._activity.area.set_stroke_color(new_color)

    def _on_signal_undo_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    def _on_signal_redo_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    def _on_signal_select_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    def _on_signal_action_saved_cb(self, widget, data=None):
        self._verify_sensitive_buttons()

    def _verify_sensitive_buttons(self):
        # Check if there is an area selected or if the "stamp" tool is
        # being used
        sensitive = self._activity.area.is_selected() or \
            self.properties['name'] == 'stamp'
        self._tool_stamp.set_sensitive(sensitive)


class ButtonFillColor(ColorToolButton):
    """Class to manage the Fill Color of a Button"""

    def __init__(self, activity):
        ColorToolButton.__init__(self)
        self._activity = activity
        self.properties = self._activity.area.tool
        self.connect('notify::color', self._color_button_cb)

    def _color_button_cb(self, widget, pspec):
        color = self.get_color()
        self.set_fill_color(color)

    def set_fill_color(self, color):
        self._activity.area.set_fill_color(color)

    def create_palette(self):
        self._palette = self.get_child().create_palette()
        color_palette_hbox = self._palette._picker_hbox

        content_box = Gtk.VBox()

        # Fill option
        fill_checkbutton = Gtk.CheckButton(_('Fill'))
        fill_checkbutton.set_active(self.properties['fill'])
        fill_checkbutton.connect('toggled',
            self._on_fill_checkbutton_toggled)
        content_box.pack_start(fill_checkbutton, True, True, 0)

        keep_aspect_checkbutton = Gtk.CheckButton(_('Keep aspect'))
        logging.error('Create palette : tool name %s', self.properties['name'])
        ratio = self._activity.area.keep_shape_ratio
        keep_aspect_checkbutton.set_active(ratio)
        keep_aspect_checkbutton.connect('toggled',
            self._on_keep_aspect_checkbutton_toggled)
        content_box.pack_start(keep_aspect_checkbutton, True, True, 0)

        # We want choose the number of sides to our polygon
        spin = Gtk.SpinButton()

        # This is where we set restrictions for sides in Regular Polygon:
        # Initial value, minimum value, maximum value, step
        adj = Gtk.Adjustment(self.properties['vertices'], 3.0, 50.0, 1.0)
        spin.set_adjustment(adj)
        spin.set_numeric(True)

        label = Gtk.Label(label=_('Sides: '))
        #For stars
        #label = Gtk.Label(label=_('Points: '))

        hbox = Gtk.HBox()
        hbox.show_all()
        hbox.pack_start(label, True, True, 0)
        hbox.pack_start(spin, True, True, 0)

        content_box.pack_start(hbox, True, True, 0)
        hbox.show_all()
        spin.connect('value-changed', self._on_vertices_value_changed)

        color_palette_hbox.pack_start(Gtk.VSeparator(), True, True,
                                     padding=style.DEFAULT_SPACING)
        color_palette_hbox.pack_start(content_box, True, True, 0)
        color_palette_hbox.show_all()
        return self._palette

    def _on_vertices_value_changed(self, spinbutton):
        self.properties['vertices'] = spinbutton.get_value_as_int()

    def _on_fill_checkbutton_toggled(self, checkbutton):
        logging.debug('Checkbutton is Active: %s', checkbutton.get_active())
        self.properties['fill'] = checkbutton.get_active()

    def _on_keep_aspect_checkbutton_toggled(self, checkbutton):
        self._activity.area.keep_shape_ratio = checkbutton.get_active()


##Make the Shapes Toolbar
class ShapesToolbar(Gtk.Toolbar):

    _SHAPE_ARROW_NAME = 'arrow'
    _SHAPE_CURVE_NAME = 'curve'
    _SHAPE_ELLIPSE_NAME = 'ellipse'
    _SHAPE_FREEFORM_NAME = 'freeform'
    _SHAPE_HEART_NAME = 'heart'
    _SHAPE_LINE_NAME = 'line'
    _SHAPE_PARALLELOGRAM_NAME = 'parallelogram'
    _SHAPE_POLYGON_NAME = 'polygon_regular'
    _SHAPE_RECTANGLE_NAME = 'rectangle'
    _SHAPE_STAR_NAME = 'star'
    _SHAPE_TRAPEZOID_NAME = 'trapezoid'
    _SHAPE_TRIANGLE_NAME = 'triangle'

    ##The Constructor
    def __init__(self, activity):
        GObject.GObject.__init__(self)

        self._activity = activity
        self.properties = self._activity.area.tool

        self._fill_color = ButtonFillColor(activity)
        self._fill_color.set_icon_name('icon-fill')
        self._fill_color.set_title(_('Shapes properties'))
        item = Gtk.ToolItem()
        item.add(self._fill_color)
        self.insert(item, -1)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        self.insert(separator, -1)

        # self._configure_palette_shape_ellipse()

        self._shape_ellipse = DrawToolButton('tool-shape-ellipse',
            activity.tool_group, _('Ellipse'))
        self.insert(self._shape_ellipse, -1)

        self._shape_rectangle = DrawToolButton('tool-shape-rectangle',
            activity.tool_group, _('Rectangle'))
        self.insert(self._shape_rectangle, -1)

        self._shape_line = DrawToolButton('tool-shape-line',
            activity.tool_group, _('Line'))
        self.insert(self._shape_line, -1)

        self._shape_freeform = DrawToolButton('tool-shape-freeform',
            activity.tool_group, _('Free form'))
        self.insert(self._shape_freeform, -1)

        self._shape_polygon = DrawToolButton('tool-shape-polygon',
            activity.tool_group, _('Polygon'))
        self.insert(self._shape_polygon, -1)

        self._shape_heart = DrawToolButton('tool-shape-heart',
            activity.tool_group, _('Heart'))
        self.insert(self._shape_heart, -1)

        self._shape_parallelogram = DrawToolButton('tool-shape-parallelogram',
            activity.tool_group, _('Parallelogram'))
        self.insert(self._shape_parallelogram, -1)

        self._shape_arrow = DrawToolButton('tool-shape-arrow',
            activity.tool_group, _('Arrow'))
        self.insert(self._shape_arrow, -1)

        self._shape_star = DrawToolButton('tool-shape-star',
            activity.tool_group, _('Star'))
        self.insert(self._shape_star, -1)

        self._shape_trapezoid = DrawToolButton('tool-shape-trapezoid',
            activity.tool_group, _('Trapezoid'))
        self.insert(self._shape_trapezoid, -1)

        self._shape_triangle = DrawToolButton('tool-shape-triangle',
            activity.tool_group, _('Triangle'))
        self.insert(self._shape_triangle, -1)

        self._shape_arrow.connect('clicked', self.set_tool, self.properties,
            self._SHAPE_ARROW_NAME)
        self._shape_ellipse.connect('clicked', self.set_tool, self.properties,
            self._SHAPE_ELLIPSE_NAME)
        self._shape_freeform.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_FREEFORM_NAME)
        self._shape_heart.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_HEART_NAME)
        self._shape_line.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_LINE_NAME)
        self._shape_parallelogram.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_PARALLELOGRAM_NAME)
        self._shape_polygon.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_POLYGON_NAME)
        self._shape_rectangle.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_RECTANGLE_NAME)
        self._shape_star.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_STAR_NAME)
        self._shape_trapezoid.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_TRAPEZOID_NAME)
        self._shape_triangle.connect('clicked', self.set_tool,
            self.properties, self._SHAPE_TRIANGLE_NAME)
        self.show_all()

    def set_tool(self, widget, tool, tool_name):
        tool['name'] = tool_name
        self._activity.area.set_tool(tool)


##Make the Text Toolbar
class TextToolbar(Gtk.Toolbar):

    _ACTION_TEXT_NAME = 'text'

    def __init__(self, activity):
        GObject.GObject.__init__(self)

        self._activity = activity
        self.properties = self._activity.area.tool

        self._text = DrawToolButton('text', activity.tool_group, _('Type'))
        self.insert(self._text, -1)
        self._text.connect('clicked', self.set_tool, self._ACTION_TEXT_NAME)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        self.insert(separator, -1)

        self._bold = ToggleToolButton('format-text-bold')
        self.insert(self._bold, -1)
        self._bold.show()
        self._bold.connect('clicked', self.__bold_bt_cb)

        self._italic = ToggleToolButton('format-text-italic')
        self.insert(self._italic, -1)
        self._italic.show()
        self._italic.connect('clicked', self.__italic_bt_cb)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        self.insert(separator, -1)

        fd = activity.area.get_font_description()

        self._font_size_combo = Gtk.ComboBoxText()
        self._font_sizes = ['8', '10', '12', '14', '16', '20',
                            '22', '24', '26', '28', '36', '48', '72']
        self._font_size_changed_id = self._font_size_combo.connect('changed',
                self.__font_size_changed_cb)
        for i, s in enumerate(self._font_sizes):
            self._font_size_combo.append_text(s)
            if int(s) == (fd.get_size() /Pango.SCALE):
                self._font_size_combo.set_active(i)

        tool_item = ToolComboBox(self._font_size_combo)
        self.insert(tool_item, -1)

        self._font_combo = FontComboBox()
        self._fonts_changed_id = self._font_combo.connect('changed',
                self.__font_changed_cb)
        font_name = fd.get_family()
        self._font_combo.set_font_name(font_name)
        tool_item = ToolComboBox(self._font_combo)
        self.insert(tool_item, -1)
        self.show_all()

    def __bold_bt_cb(self, button):
        fd = self._activity.area.get_font_description()
        if button.get_active():
            fd.set_weight(Pango.Weight.BOLD)
        else:
            fd.set_weight(Pango.Weight.NORMAL)
        self._activity.area.set_font_description(fd)

    def __italic_bt_cb(self, button):
        fd = self._activity.area.get_font_description()
        if button.get_active():
            fd.set_style(Pango.Style.ITALIC)
        else:
            fd.set_style(Pango.Style.NORMAL)
        self._activity.area.set_font_description(fd)

    def __font_size_changed_cb(self, combo):
        fd = self._activity.area.get_font_description()
        value = self.get_active_text(combo)
        fd.set_size(int(value) * Pango.SCALE)
        self._activity.area.set_font_description(fd)

    def __font_changed_cb(self, combo):
        fd = self._activity.area.get_font_description()
        font_name = combo.get_font_name()
        fd.set_family(font_name)
        self._activity.area.set_font_description(fd)

    def get_active_text(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]

    def set_tool(self, widget, tool_name):
        self.properties['name'] = tool_name
        self._activity.area.set_tool(self.properties)


##Make the Images Toolbar
class ImageToolbar(Gtk.Toolbar):

    _EFFECT_RAINBOW_NAME = 'rainbow'

    def __init__(self, activity):
        GObject.GObject.__init__(self)
        self._activity = activity
        self.properties = self._activity.area.tool

        self._object_insert = ToolButton('insert-picture')
        self.insert(self._object_insert, -1)
        self._object_insert.set_tooltip(_('Insert Image'))

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        self.insert(separator, -1)

        self.width_percent = 1.
        self.height_percent = 1.

        is_selected = self._activity.area.is_selected()

        self._object_rotate_left = ToolButton('object-rotate-left')
        self.insert(self._object_rotate_left, -1)
        self._object_rotate_left.set_tooltip(_('Rotate Left'))

        self._object_rotate_right = ToolButton('object-rotate-right')
        self.insert(self._object_rotate_right, -1)
        self._object_rotate_right.set_tooltip(_('Rotate Right'))

        self._mirror_horizontal = ToolButton('mirror-horizontal')
        self.insert(self._mirror_horizontal, -1)
        self._mirror_horizontal.show()
        self._mirror_horizontal.set_tooltip(_('Horizontal Mirror'))

        self._mirror_vertical = ToolButton('mirror-vertical')
        self.insert(self._mirror_vertical, -1)
        self._mirror_vertical.show()
        self._mirror_vertical.set_tooltip(_('Vertical Mirror'))

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        self.insert(separator, -1)

        self._effect_grayscale = ToolButton('effect-grayscale')
        self.insert(self._effect_grayscale, -1)
        self._effect_grayscale.set_tooltip(_('Grayscale'))

        self._effect_rainbow = DrawToolButton('effect-rainbow',
            activity.tool_group, _('Rainbow'))
        self.insert(self._effect_rainbow, -1)

        self._invert_colors = ToolButton('invert-colors')
        self.insert(self._invert_colors, -1)
        self._invert_colors.set_tooltip(_('Invert Colors'))

        self._object_insert.connect('clicked', self.insertImage, activity)
        self._object_rotate_left.connect('clicked', self.rotate_left,
            activity)
        self._object_rotate_right.connect('clicked', self.rotate_right,
            activity)
        self._mirror_vertical.connect('clicked', self.mirror_vertical)
        self._mirror_horizontal.connect('clicked', self.mirror_horizontal)

        self._effect_grayscale.connect('clicked', self.grayscale)
        self._effect_rainbow.connect('clicked', self.rainbow)
        self._invert_colors.connect('clicked', self.invert_colors)

        self.show_all()

    def rotate_left(self, widget, activity):
        activity.area.rotate_left(activity.area)

    def rotate_right(self, widget, activity):
        activity.area.rotate_right(activity.area)

    def mirror_horizontal(self, widget):
        self._activity.area.mirror(widget)

    def mirror_vertical(self, widget):
        self._activity.area.mirror(widget, horizontal=False)

    def insertImage(self, widget, activity):
        chooser = ObjectChooser(self._activity, what_filter='Image')
        try:
            result = chooser.run()
            if result == Gtk.ResponseType.ACCEPT:
                logging.debug('ObjectChooser: %r',
                        chooser.get_selected_object())
                jobject = chooser.get_selected_object()
                if jobject and jobject.file_path:
                    self._activity.area.load_image(jobject.file_path)
        finally:
            chooser.destroy()
            del chooser

    ##Make the colors be in grayscale
    def grayscale(self, widget):
        self._activity.area.grayscale(widget)

    ##Like the brush, but change it color when painting
    def rainbow(self, widget):
        self.properties['name'] = self._EFFECT_RAINBOW_NAME

    def invert_colors(self, widget):
        self._activity.area.invert_colors(widget)
