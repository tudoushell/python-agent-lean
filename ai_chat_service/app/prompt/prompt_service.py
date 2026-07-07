from dataclasses import dataclass
from pathlib import Path

from ai_chat_service.app.core.config import get_settings
from ai_chat_service.app.core.exception import AppException


@dataclass(frozen=True)
class PromptTemplate:
    scene: str
    system_prompt: str
    user_template: str


class PromptService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.prompt_root = Path(__file__).resolve().parent.parent.parent / "prompts"

    def get_template(self, scene: str | None) -> PromptTemplate:
        real_scene = self._resolve_scene(scene)

        system_prompt = self._read_prompt_file(real_scene, "system.md")
        user_prompt = self._read_prompt_file(real_scene, "user.md")
        return PromptTemplate(real_scene, system_prompt, user_prompt)

    def render_user_prompt(self, user_template: str, question: str) -> str:
        return user_template.replace("{question}", question)

    def _resolve_scene(self, scene: str | None) -> str:
        if scene is None or scene == "":
            return self.settings.default_scene
        return scene.strip()

    def _read_prompt_file(self, real_scene: str, file_name: str) -> str:
        file_path = self.prompt_root / real_scene / file_name
        if not file_path.exists():
            raise AppException(
                message=f"File {file_path} does not exist",
                code="PROMPT_FILE_NOT_FOUND",
                status_code=404
            )
        return file_path.read_text(encoding="utf-8").strip(

        )


if __name__ == "__main__":
    prompt_service = PromptService()
    prompt_template =  prompt_service.get_template("general")
    print(prompt_template.system_prompt)
    print(prompt_template.user_template)
