"""
Testes automatizados para validação do prompt otimizado (v2).

Os testes validam a ESTRUTURA do arquivo prompts/bug_to_user_story_v2.yml,
sem depender de chaves de API ou de chamadas ao LangSmith — rodam 100% offline.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path para reaproveitar validate_prompt_structure
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Retorna o bloco do prompt v2 já desaninhado da chave raiz."""
    assert V2_PATH.exists(), f"Arquivo do prompt otimizado não encontrado: {V2_PATH}"
    data = load_prompts(str(V2_PATH))
    assert isinstance(data, dict) and data, "YAML vazio ou inválido"
    # O conteúdo fica sob a chave 'bug_to_user_story_v2'
    return data.get("bug_to_user_story_v2", data)


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        system_prompt = prompt_data.get("system_prompt", "")
        assert system_prompt and system_prompt.strip(), "system_prompt ausente ou vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex.: "Você é um Product Manager")."""
        system_prompt = prompt_data.get("system_prompt", "").lower()
        assert "você é" in system_prompt, "O prompt não define uma persona (Role Prompting)"

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou de User Story padrão."""
        system_prompt = prompt_data.get("system_prompt", "").lower()
        format_markers = ["critérios de aceitação", "como um", "para que", "dado que"]
        assert any(marker in system_prompt for marker in format_markers), \
            "O prompt não especifica o formato esperado da User Story"

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data.get("system_prompt", "").lower()
        assert "exemplo" in system_prompt and "relato:" in system_prompt, \
            "O prompt não contém exemplos few-shot de entrada/saída"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que não ficou nenhum marcador TODO no texto do prompt.

        A checagem é case-sensitive de propósito: o marcador é o literal
        'TODO'/'[TODO]' em maiúsculas. Palavras em português como 'todas' ou
        'toda' (minúsculas) não devem disparar falso-positivo.
        """
        text = (prompt_data.get("system_prompt", "") + " " +
                str(prompt_data.get("user_prompt", "")))
        assert "[TODO]" not in text and "TODO" not in text, "Ainda há marcador TODO no prompt"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (via metadados do YAML) se ao menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list) and len(techniques) >= 2, \
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"

    def test_validate_prompt_structure_helper(self, prompt_data):
        """Reaproveita o validador oficial de utils.py como checagem extra."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
