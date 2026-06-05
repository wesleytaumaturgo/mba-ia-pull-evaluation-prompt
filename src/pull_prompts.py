"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt base de baixa qualidade (leonanluppi/bug_to_user_story_v1)
3. Salva localmente em prompts/bug_to_user_story_v1.yml

Usa a serialização nativa do LangChain para extrair o conteúdo do prompt.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Prompt base (ruim) publicado no Hub que deve ser otimizado
BASE_PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def extract_prompt_text(prompt_obj) -> dict:
    """
    Extrai um dicionário serializável (system/user/template) a partir do
    objeto retornado por hub.pull, lidando com ChatPromptTemplate e PromptTemplate.
    """
    system_prompt = ""
    user_prompt = ""
    raw_template = ""

    # ChatPromptTemplate: tem uma lista de mensagens
    messages = getattr(prompt_obj, "messages", None)
    if messages:
        for message in messages:
            template = getattr(getattr(message, "prompt", None), "template", None)
            role = type(message).__name__.lower()
            if template is None:
                continue
            if "system" in role:
                system_prompt += template
            elif "human" in role or "user" in role:
                user_prompt += template
            else:
                raw_template += template
    else:
        # PromptTemplate simples
        raw_template = getattr(prompt_obj, "template", str(prompt_obj))

    return {
        "bug_to_user_story_v1": {
            "description": "Prompt base (baixa qualidade) puxado do LangSmith Hub para otimização.",
            "source": BASE_PROMPT_NAME,
            "system_prompt": system_prompt or raw_template,
            "user_prompt": user_prompt or "{bug_report}",
            "version": "v1",
        }
    }


def pull_prompts_from_langsmith() -> bool:
    """Faz pull do prompt base e salva localmente em YAML."""
    print(f"   Puxando prompt do Hub: {BASE_PROMPT_NAME}")
    try:
        prompt_obj = hub.pull(BASE_PROMPT_NAME)
    except Exception as e:
        print(f"\n❌ Erro ao puxar '{BASE_PROMPT_NAME}' do LangSmith Hub: {e}")
        print("\nVerifique:")
        print("  - LANGSMITH_API_KEY está configurada corretamente no .env")
        print("  - Você tem acesso ao workspace do LangSmith")
        print("  - Sua conexão com a internet está funcionando")
        return False

    print("   ✓ Prompt carregado do Hub")

    data = extract_prompt_text(prompt_obj)

    if save_yaml(data, OUTPUT_PATH):
        print(f"   ✓ Prompt salvo localmente em: {OUTPUT_PATH}")
        return True

    print(f"   ❌ Falha ao salvar {OUTPUT_PATH}")
    return False


def main():
    """Função principal."""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    ok = pull_prompts_from_langsmith()

    if ok:
        print("\n✅ Pull concluído. Analise o prompt base e otimize em:")
        print("   prompts/bug_to_user_story_v2.yml")
        return 0

    print("\n❌ Pull falhou. Veja as mensagens acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
