"""
Script para fazer push do prompt otimizado ao LangSmith Prompt Hub.

Este script:
1. Lê o prompt otimizado de prompts/bug_to_user_story_v2.yml
2. Valida a estrutura do prompt
3. Monta um ChatPromptTemplate (System + User prompt)
4. Faz push PÚBLICO para o Hub como {USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

V2_PATH = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple:
    """Valida a estrutura básica do prompt reaproveitando o validador de utils."""
    return validate_prompt_structure(prompt_data)


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Monta um ChatPromptTemplate a partir do system_prompt e user_prompt."""
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt") or "{bug_report}"

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO)."""
    chat_prompt = build_chat_prompt(prompt_data)
    description = prompt_data.get("description", "")

    # A assinatura de hub.push variou entre versões do langchain/langsmith.
    # Tentamos com o flag de público; se a versão não aceitar, fazemos fallback.
    attempts = [
        dict(new_repo_is_public=True, new_repo_description=description),
        dict(is_public=True),
        dict(),  # fallback: push sem flag — marcar público manualmente no dashboard
    ]

    last_error = None
    for kwargs in attempts:
        try:
            url = hub.push(prompt_name, chat_prompt, **kwargs)
            print(f"   ✓ Push realizado: {prompt_name}")
            if url:
                print(f"   🔗 URL: {url}")
            if "new_repo_is_public" not in kwargs and "is_public" not in kwargs:
                print("   ⚠️  Este push não enviou o flag de visibilidade.")
                print("       Marque o prompt como PÚBLICO manualmente no dashboard (ícone de cadeado).")
            return True
        except TypeError as e:
            # parâmetro não suportado nesta versão — tenta o próximo conjunto de kwargs
            last_error = e
            continue
        except Exception as e:
            last_error = e
            break

    print(f"\n❌ Erro ao fazer push de '{prompt_name}': {last_error}")
    print("\nVerifique:")
    print("  - LANGSMITH_API_KEY e USERNAME_LANGSMITH_HUB no .env")
    print("  - O nome do repositório está no formato {username}/{prompt}")
    return False


def main():
    """Função principal."""
    print_section_header("PUSH DO PROMPT OTIMIZADO PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(V2_PATH)
    if not data:
        print(f"❌ Não foi possível carregar {V2_PATH}")
        return 1

    prompt_data = data.get(PROMPT_KEY, data)

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Validação do prompt falhou:")
        for err in errors:
            print(f"   - {err}")
        return 1
    print("   ✓ Prompt validado")

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/{PROMPT_KEY}"

    if push_prompt_to_langsmith(prompt_name, prompt_data):
        print("\n✅ Push concluído. Agora avalie com:")
        print("   python src/evaluate.py")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
