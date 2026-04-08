"""Unit tests for latex_builder.config.settings.Config."""

from pathlib import Path

from latex_builder.config.settings import Config


class TestConfigDefaults:
    """Test Config default values."""

    def test_default_values(self):
        config = Config()
        assert config.repo_path == Path(".")
        assert config.tex_file == "main.tex"
        assert config.compiler == "xelatex"
        assert config.compare_with is None
        assert config.revision_file == "variables/revision.tex"
        assert config.output_dir == Path("output")
        assert config.build_dir == Path("build")
        assert config.no_diff is False
        assert config.diff_only is False
        assert config.verbose is False
        assert config.quiet is False


class TestConfigPostInit:
    """Test Config.__post_init__ type coercion."""

    def test_string_repo_path_converted_to_path(self):
        config = Config(repo_path="/tmp/test")
        assert isinstance(config.repo_path, Path)
        assert config.repo_path.is_absolute()

    def test_string_output_dir_converted_to_path(self):
        config = Config(output_dir="my_output")
        assert isinstance(config.output_dir, Path)
        assert config.output_dir == Path("my_output")

    def test_string_build_dir_converted_to_path(self):
        config = Config(build_dir="my_build")
        assert isinstance(config.build_dir, Path)
        assert config.build_dir == Path("my_build")

    def test_path_objects_unchanged(self):
        p = Path("/some/path")
        config = Config(repo_path=p, output_dir=p, build_dir=p)
        assert config.repo_path == p
        assert config.output_dir == p
        assert config.build_dir == p

    def test_repo_path_resolved_to_absolute(self):
        config = Config(repo_path="relative/path")
        assert config.repo_path.is_absolute()


class TestConfigRevisionPath:
    """Test Config.revision_path property."""

    def test_revision_path_returns_revision_file(self):
        config = Config(revision_file="custom/path.tex")
        assert config.revision_path == "custom/path.tex"

    def test_revision_path_default(self):
        config = Config()
        assert config.revision_path == "variables/revision.tex"
