from livetranslate.translate.prompts import build_system_prompt, build_user_prompt, clean_translation, load_glossary


def test_clean_translation_variants():
    assert clean_translation('"Xin chào"') == "Xin chào"
    assert clean_translation("Translation: Xin chào") == "Xin chào"
    assert clean_translation("[skip]") == ""
    assert clean_translation(" skip ") == ""
    assert clean_translation("```\nXin chào\n```") == "Xin chào"
    assert clean_translation("") == ""


def test_system_prompt_mentions_languages_and_glossary(tmp_path):
    g = tmp_path / "g.txt"
    g.write_text("# chú thích\nGPU = card đồ họa\nlatency\tđộ trễ\n", encoding="utf-8")
    glossary = load_glossary(str(g))
    assert glossary == {"GPU": "card đồ họa", "latency": "độ trễ"}
    sp = build_system_prompt("vi", "en", glossary)
    assert "English" in sp and "Vietnamese" in sp
    assert "GPU => card đồ họa" in sp


def test_user_prompt_includes_context():
    up = build_user_prompt("How are you?", [("Hello", "Xin chào")])
    assert "Xin chào" in up
    assert up.rstrip().endswith("How are you?")
