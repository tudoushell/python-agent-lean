from abc import abstractmethod, ABC
from typing import Generator


class llm_scen_client(ABC):
    def chat(self, scene: str, message: str) -> Generator[str, None, None]:
        self.build_scene(scene)

    @abstractmethod
    def build_scene(self, scene: str) -> Generator[str, None, None]:
        pass




