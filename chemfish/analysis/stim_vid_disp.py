from PIL import Image, ImageDraw
import skvideo.io
import cv2
from kale.core.core_imports import *
from kale.model.stim_frames import *
from kale.viz.stim_plots import *
from kale.caches.audio_caches import *
from kale.caches.video_cache import *
from kale.viz.kvrc import *


class IncorrectVidDimensionsError(Exception):
    pass


class VideoStimFrameDisplayer:
    def __init__(self, run_id: RunLike, input_dict: Dict = None, output_dict: Dict = None):
        self.inputdict = {} if not input_dict else input_dict
        self.outputdict = {} if not output_dict else output_dict
        VideoCache().download(run_id)
        self.vid_path = VideoCache().path_of(run_id)
        self.run = Tools.run(run_id)
        self.b_id = self.run.experiment.battery.id
        self.generation = ValarTools.generation_of(self.run)
        if not self.generation.is_sauronx():
            raise SauronxOnlyError("Run r{} is legacy".format(self.run.id))

    def _create_stimplot(self, start_ms: int, end_ms: int):
        # extract relevant batterystimframedata
        bsf = BatteryStimFrame.of(self.b_id, start_ms=start_ms, end_ms=end_ms)
        bsf.expand_audio_inplace(
            AudioStimulusCache().load_waveform, ValarTools.battery_is_legacy(self.b_id)
        )
        # Plot stimframeplot
        with KVRC.using(
            rasterize_traces=True, trace_width=8, trace_height=1,
        ):
            fig_axes = StimframesPlotter().plot(starts_at_ms=start_ms, stimframes=bsf)
        # Extract StimframePlotter figure from the canvas
        stim_fig = fig_axes.figure
        stim_fig.canvas.draw()
        fig_arr = np.frombuffer(stim_fig.canvas.tostring_rgb(), dtype=np.uint8)
        return fig_arr.reshape(stim_fig.canvas.get_width_height()[::-1] + (3,))

    def _check_vid_dims(self, cv_video: cv2.VideoCapture):
        vid_w = int(cv_video.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_h = int(cv_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        x0, y0, x1, y1 = ValarTools.toml_items(self.run)[
            "sauron.hardware.camera.plate.{}.roi".format(self.run.plate.plate_type_id)
        ]
        evid_dim = (x1 - x0, y1 - y0)
        if (evid_dim[0] != vid_w) and evid_dim[1] != vid_h:
            raise IncorrectVidDimensionsError(
                "Video has wrong dimensions. Expected: {0} Actual: {1}".format(
                    evid_dim, (vid_w, vid_h)
                )
            )
        return vid_w, vid_h

    def _init_vid_writer(self, cv_video: cv2.VideoCapture, out_path: str):
        vid_w, vid_h = self._check_vid_dims(cv_video)
        fps = int(cv_video.get(cv2.CAP_PROP_FPS))
        if "-framerate" not in self.inputdict:
            self.inputdict["-framerate"] = "{}".format(fps)
        if "-video_size" not in self.inputdict:
            self.inputdict["-video_size"] = "{0}x{1}".format(vid_w, vid_h)
        if "-pixel_format" not in self.outputdict:
            self.outputdict["-pixel_format"] = "gray"
        if "-vcodec" not in self.outputdict:
            self.outputdict["-vcodec"] = "libx265"
        if "-g" not in self.outputdict:
            self.outputdict["-g"] = "100"
        if "-preset" not in self.outputdict:
            self.outputdict["-preset"] = "veryfast"
        if "-r" not in self.outputdict:
            self.outputdict["-r"] = str(fps)
        writer = skvideo.io.FFmpegWriter(
            out_path, inputdict=self.inputdict, outputdict=self.outputdict
        )
        return writer

    def make_vid(
        self,
        video_output_path: str,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        disp_prog: bool = True,
    ):
        cv_vid = cv2.VideoCapture(str(self.vid_path.resolve()))
        fps = int(cv_vid.get(cv2.CAP_PROP_FPS))
        # Get Start and End frames'
        start_s = start_ms / 1000 if start_ms else 0
        end_s = (
            end_ms / 1000
            if end_ms
            else cv_vid.get(cv2.CAP_PROP_FRAME_COUNT) / cv_vid.get(cv2.CAP_PROP_FPS)
        )
        start_frame = start_s * fps if start_s else 0
        end_frame = end_s * fps if end_s else int(cv_vid.get(cv2.CAP_PROP_FRAME_COUNT))
        rgb_img = self._create_stimplot(start_s * 1000, end_s * 1000)
        count = 0
        success = True
        writer = self._init_vid_writer(cv_vid, video_output_path)
        # TODO Computationally find start and end Pixels? This is currently hardcoded for a figure of size 1600 x 1068
        start_pxl = 46
        end_pxl = 1576
        vid_total_frames = int(end_frame - start_frame)
        stim_fig_width = end_pxl - start_pxl
        cv_vid.set(1, start_frame)  # Set Camera Frame
        while success & (count < vid_total_frames):
            fig_img = Image.fromarray(rgb_img, "RGB")
            draw = ImageDraw.Draw(fig_img)
            x_coord = stim_fig_width * count / vid_total_frames
            draw.line((x_coord + start_pxl, 20) + (x_coord + start_pxl, 110), fill=0, width=3)
            success, image = cv_vid.read()
            writer.writeFrame(np.vstack([image, np.array(fig_img)]))
            count += 1
            # Progress Bar
            if disp_prog:
                sys.stdout.write("Video progress: %d%%   \r" % ((count * 100.0) / vid_total_frames))
                sys.stdout.flush()
        writer.close()
        return


__all__ = ["VideoStimFrameDisplayer"]
