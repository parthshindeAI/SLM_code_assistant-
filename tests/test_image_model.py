import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import torch

from src import image_model


class ImageModelTests(unittest.TestCase):
    def test_existing_default_cache_is_used_without_network_download(self):
        pipeline = Mock()
        pipeline.to.return_value = pipeline
        diffusers = types.SimpleNamespace(AutoPipelineForText2Image=Mock())
        diffusers.AutoPipelineForText2Image.from_pretrained.return_value = pipeline

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / ".cache" / "huggingface" / "hub"
            (cache_dir / "models--stabilityai--sd-turbo").mkdir(parents=True)
            with (
                patch.dict(sys.modules, {"diffusers": diffusers}),
                patch.object(Path, "home", return_value=Path(temp_dir)),
            ):
                loaded = image_model._load_pipeline(
                    image_model.MODEL_ID, "cuda", torch.float16
                )

        self.assertIs(loaded, pipeline)
        diffusers.AutoPipelineForText2Image.from_pretrained.assert_called_once_with(
            image_model.MODEL_ID,
            torch_dtype=torch.float16,
            cache_dir=str(cache_dir),
            local_files_only=True,
        )
        pipeline.to.assert_called_once_with("cuda")

    def test_missing_default_cache_uses_configured_huggingface_cache(self):
        pipeline = Mock()
        diffusers = types.SimpleNamespace(AutoPipelineForText2Image=Mock())
        diffusers.AutoPipelineForText2Image.from_pretrained.return_value = pipeline

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(sys.modules, {"diffusers": diffusers}),
            patch.object(Path, "home", return_value=Path(temp_dir)),
        ):
            image_model._load_pipeline(
                image_model.MODEL_ID, "cpu", torch.float32
            )

        diffusers.AutoPipelineForText2Image.from_pretrained.assert_called_once_with(
            image_model.MODEL_ID, torch_dtype=torch.float32
        )
        pipeline.to.assert_called_once_with("cpu")

    def test_generate_image_uses_turbo_sampling_settings(self):
        pipeline = Mock()
        generated_image = Mock()
        generated_image.save.side_effect = lambda path: Path(path).touch()
        pipeline.return_value.images = [generated_image]

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(image_model, "_PIPELINE", pipeline),
                patch.object(image_model, "_PIPELINE_NAME", image_model.MODEL_ID),
                patch.object(image_model, "IMAGE_DIR", Path(temp_dir)),
                patch.object(
                    image_model,
                    "device_info",
                    return_value=("GPU", image_model.MODEL_ID),
                ),
                patch("time.strftime", return_value="20261029-000000"),
            ):
                file_path, caption = image_model.generate_image(
                    "a small red house", steps=4, size=512
                )
            self.assertTrue(file_path.exists())

        pipeline.assert_called_once_with(
            prompt="a small red house",
            num_inference_steps=4,
            guidance_scale=0.0,
            height=512,
            width=512,
        )
        generated_image.save.assert_called_once_with(str(file_path))
        self.assertNotIn("LCM-LoRA", caption)


if __name__ == "__main__":
    unittest.main()
