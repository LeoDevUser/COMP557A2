import moderngl as mgl
from pyglm import glm
from Scene import Scene, Camera

class ViewPostPerspective():
    def __init__(self, scene: Scene, camera: Camera, ctx: mgl.Context ):
        self.scene = scene
        self.camera = camera
        self.ctx = ctx

    def paintGL(self, aspect_ratio):
        self.ctx.enable(mgl.DEPTH_TEST)
        self.ctx.clear(0.2,0.2,0.3,depth=1) # keep farthest in post persective view 

        # set up projection and view matrix for the post-projection view
        V = self.camera.V = glm.translate(glm.mat4(1), glm.vec3(0, 0, -self.camera.distance)) * self.camera.R
        P = self.camera.P = glm.perspective(glm.radians(60.0), aspect_ratio, 0.1, 100.0)

        # Modelling transformation is the main camera V and P, along with a reflection in Z to account for handedness flip
        reflect_Z = glm.mat4(1)
        reflect_Z[2,2] = -1  # reflect in Z to account for handedness flip in post projection view :/
        modelling_transformation = reflect_Z * self.scene.main_view_camera.P * self.scene.main_view_camera.V
        mvp =  P * V * modelling_transformation		
        self.scene.prog_shadow_map['u_mvp'].write( mvp ) # use post perspective 

        # Despite the modeling transform above, do lighting as if for the main camera view
        self.scene.prog_shadow_map['u_mv'].write( self.scene.main_view_camera.V ) # For transforming normals and verticies to camera view		
        light_pos = self.scene.get_light_pos_in_view( self.scene.main_view_camera.V ) 
        self.scene.prog_shadow_map['u_light_pos'].write(light_pos)
        self.scene.prog_shadow_map['u_use_lighting'] = True		

        self.scene.render_for_view()

        # Draw the frustums and axes as required by the assignment specification
        self.scene.prog_shadow_map['u_use_lighting'] = False
        self.ctx.enable(mgl.BLEND) # slightly nicer lines

        # TODO: OBJECTIVE: draw frustums and axes for this view as required by the assignment specification

        # draw the origin of the CCV frame 
        #M = glm.mat4(1) # TODO: compute the appropriate matrix to draw the CCV axis for this view
        M = mvp * glm.inverse(self.scene.post_projection_camera.V)
        self.scene.prog_shadow_map['u_mvp'].write(M)
        self.scene.axis.render()

        if self.scene.controls.show_light_camera:		

            #M = glm.mat4(1) # TODO: compute the appropriate matrix to draw the light camera frustum for this view
            M = mvp * glm.inverse(self.scene.light_view_camera.V) * glm.inverse(self.scene.light_view_camera.P)
            self.scene.prog_shadow_map['u_mvp'].write(M)
            self.scene.prog_shadow_map['u_color'] = (1, 1, 0, 0.75) # make light frustum yellow
            self.scene.render_cube_and_grid()

            #M = glm.mat4(1) # TODO: compute the appropriate matrix to draw the light camera axis for this view
            M = mvp * glm.inverse(self.scene.light_view_camera.V)
            self.scene.prog_shadow_map['u_mvp'].write(M)
            self.scene.render_axis()

        if self.scene.controls.show_main_camera:			

            #M = glm.mat4(1) # TODO: compute the appropriate matrix to draw the main camera frustum for this view
            M = mvp * glm.inverse(self.scene.main_view_camera.V) * glm.inverse(self.scene.main_view_camera.P)
            self.scene.prog_shadow_map['u_mvp'].write(M)
            self.scene.prog_shadow_map['u_color'] = (1, 1, 1, 0.75)  # make main frustum white
            self.scene.render_cube()  # Frustum of main camera

            # TODO: Can you draw the main camera view axis too?
            #TODO: Explanation as to why this wont draw the main camera axis. im not sure but it has to do with the fact
            #that moving the main view camera moves the frustum and axis of the light camer view and the axis of the post-projection view
            # in the post projectiion camera view pane.
            M = mvp * glm.inverse(self.scene.main_view_camera.V)
            self.scene.prog_shadow_map['u_mvp'].write(M)
            self.scene.render_axis()

        self.ctx.disable(mgl.BLEND)
