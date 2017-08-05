bl_info = {
    "name": "Animation loop smooth tool",
    "author": "Eryk Dwornicki",
    "version": (0, 1, 1),
    "blender": (2, 78, 0),
    "location": "Graph Editor > Key > Snap nodes for smooth loop",
    "description": ("Adds an option for snapping nodes for easier animation loop smoothing."),
    "category": "Animation"}

import bpy
import sys
import random

class SmoothLoopNodes(bpy.types.Operator):
    bl_idname = "graph_key.smoothloop"
    bl_label = "Smooth animation loop"

    proportional_snap_size = bpy.props.FloatProperty(
        name = "Proportional snap size",
        description = "Proportional snap size",
        min = 0.0,
        max = sys.float_info.max,
        step = 0.01,
        default = 25,
        unit = 'AREA',
        precision = 1
    )

    def calculate_proportional_snap_factor(self, distance, size):
        if distance > size:
            return 0.0

        dist = max((size - distance) / size, 0.0)
        ts = bpy.context.tool_settings
        falloff = ts.proportional_edit_falloff
        print(falloff)
        print(dist)
        if falloff == 'SHARP':
            return dist * dist
        elif falloff == 'SMOOTH':
            return 3.0 * dist * dist - 2.0 * dist * dist * dist
        elif falloff == 'ROOT':
            return math.sqrt(dist)
        elif falloff == 'LIN':
            return dist
        elif falloff == 'CONST':
            return 1.0
        elif falloff == 'SPHERE':
            return math.sqrt(2 * dist - dist * dist)
        elif falloff == 'RANDOM':
            return random.random() * dist
        elif falloff == 'INVSQUARE':
            return dist * (2.0 - dist)
        else:
            return 1.0

    def transform_point(self, pt, deltaY):
        pt.co[1] = pt.co[1] - deltaY
        pt.handle_right[1] = pt.handle_right[1] - deltaY
        pt.handle_left[1] = pt.handle_left[1] - deltaY

    # Performs proportional snap
    def proportional_snap(self, kf_pts, delta, size, proportional_base):
        points_to_snap = len(kf_pts) - 2
        if points_to_snap < 1:
            # We have no points to snap :-(
            return

        for i in range(points_to_snap):
            index = -(2 + i)
            pt = kf_pts[index]

            dist = proportional_base - pt.co[0]
            if dist > size:
                continue

            factor = self.calculate_proportional_snap_factor(dist, size)

            self.transform_point(pt, delta * factor)

    def snap_extremes(self, curve):
        kf_pts = curve.keyframe_points
        if len(kf_pts) < 2:
            return False # not enough points to snap :-(((

        last = kf_pts[-1]
        old_co = last.co

        first = kf_pts[0]
        first_co = first.co

        if old_co[1] != first_co[1]:
            print("Snap done on curve - ", curve.data_path)

            delta = last.co[1] - first_co[1]
            self.transform_point(last, delta)
            self.proportional_snap(kf_pts, delta, self.proportional_snap_size, last.co[0])

        # To refresh graph editor reselect the curve
        curve.select = False
        curve.select = True
        return True

    def execute(self, context):
        smooth_object = bpy.context.scene.objects.active
        fcurves = smooth_object.animation_data.action.fcurves

        for curve in fcurves:
            if not curve.select:
                continue

            self.snap_extremes(curve)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        smooth_object = bpy.context.scene.objects.active

        if not smooth_object:
            self.report({'ERROR_INVALID_INPUT'}, 'Please select object which animation loop should be smoothed')
            return {'CANCELLED'}

        if not smooth_object.animation_data:
            self.report({'ERROR_INVALID_INPUT'}, 'Selected object has no animated data')
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "proportional_snap_size", text='Proportional snap size: ', icon='CURVE_NCIRCLE', slider=True, expand=True)
        layout.separator()


def menu_func(self, context):
    self.layout.operator(SmoothLoopNodes.bl_idname)

def register():
    bpy.utils.register_module(__name__)

    bpy.types.GRAPH_MT_key.prepend(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.GRAPH_MT_key.remove(menu_func)

if __name__ == "__main__":
    register()