from src.atenas.cerebro.prompts import (
    construir_system_prompt,
)


def main():

    prompt = (
        construir_system_prompt()
    )

    assert isinstance(
        prompt,
        str,
    )

    assert "ATENAS" in prompt
    assert "Benjamín" in prompt

    print()
    print("=" * 70)
    print(" PROMPT DINÁMICO DE ATENAS")
    print("=" * 70)
    print()
    print(prompt)


if __name__ == "__main__":
    main()