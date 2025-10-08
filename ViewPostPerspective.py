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

        M = mvp * glm.inverse(self.scene.post_projection_camera.V)
        self.scene.prog_shadow_map['u_mvp'].write(M)
        self.scene.axis.render()

        if self.scene.controls.show_light_camera:		

            M = mvp * glm.inverse(self.scene.light_view_camera.V) * glm.inverse(self.scene.light_view_camera.P)
            self.scene.prog_shadow_map['u_mvp'].write(M)
            self.scene.prog_shadow_map['u_color'] = (1, 1, 0, 0.75) # make light frustum yellow
            self.scene.render_cube_and_grid()

            M = mvp * glm.inverse(self.scene.light_view_camera.V)
            self.scene.prog_shadow_map['u_mvp'].write(M)
            self.scene.render_axis()

        if self.scene.controls.show_main_camera:			

            M = mvp * glm.inverse(self.scene.main_view_camera.V) * glm.inverse(self.scene.main_view_camera.P)
            self.scene.prog_shadow_map['u_mvp'].write(M)
            self.scene.prog_shadow_map['u_color'] = (1, 1, 1, 0.75)  # make main frustum white
            self.scene.render_cube()  # Frustum of main camera

            #Can you draw the main camera view axis too?

            #M = mvp * glm.inverse(self.scene.main_view_camera.V)
            #self.scene.prog_shadow_map['u_mvp'].write(M)
            #self.scene.render_axis()

            #The code above does not draw the main camera axis like it would
            #for the other cameras show_main_camera since:
            
            #mvp = P_post * V_post * reflect_Z * P_main * V_main, so
            #M = mvp * glm.inverse(self.scene.main_view_camera.V)
            #M = P_post * V_post * reflect_Z * P_main * V_main * V^-1
            #M = P_post * V_post * reflect_Z * P_main
            #Which means that we are trying to project the origin (0,0,0,1)
            #P_main * (0,0,0,1)^T = (0,0,(-2nf)/(fn),0)^T
            #So our scaling factor w becomes 0 so we cant do the perspective
            #divide since division by 0 is undefined which is why we cant draw
            #the main camera view axis

        self.ctx.disable(mgl.BLEND)
