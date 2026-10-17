"""Render the current validated mechanical screen."""
import pathlib,runpy
runpy.run_path(str(pathlib.Path(__file__).with_name("render-current-mechanical.py")),run_name="__main__")
