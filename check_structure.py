"""Project layout checker.   Run from your project folder:

    python check_structure.py          # report only
    python check_structure.py --fix    # COPY misplaced/nested files into the right place (never deletes or overwrites)
"""
import shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = ['.env.example', '.gitignore', '.streamlit/config.toml', 'README.md', 'README_CHATBOT.md', 'app.py', 'chat_app.py', 'chat_ui.py', 'chatbot/__init__.py', 'chatbot/agent.py', 'chatbot/llm.py', 'chatbot/tools.py', 'core/__init__.py', 'core/auth.py', 'core/db.py', 'core/diet.py', 'core/knowledge.py', 'core/recommend.py', 'core/risk.py', 'core/rules.py', 'core/safety.py', 'data/foods.csv', 'main.py', 'pytest.ini', 'requirements.txt', 'routers/__init__.py', 'routers/assistant.py', 'routers/predict.py', 'routers/recommendations.py', 'routers/stats.py', 'schemas.py', 'tests/test_app_flow.py', 'tests/test_assistant.py', 'tests/test_auth.py', 'tests/test_theme.py', 'theme.py', 'train_models.py', 'utils/__init__.py', 'utils/model_loader.py']
DATA_ONLY = ["data/heart_attack_prediction_dataset.csv", "models/rf_model.pkl", "models/gb_model.pkl", "models/scaler.pkl", "models/feature_names.pkl"]
SKIP = {".git", "venv", ".venv", "__pycache__", "node_modules"}


def all_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP):
            yield p.relative_to(ROOT).as_posix()


def main(fix=False):
    have = set(all_files())
    names = {}
    for e in EXPECTED:
        names.setdefault(Path(e).name, []).append(e)
    missing, relocate = [], {}
    for e in EXPECTED:
        if e in have:
            continue
        hit = [h for h in have if h.endswith("/" + e)]                                   # nested copy, e.g. mnt/.../core/auth.py
        if not hit and len(names[Path(e).name]) == 1:                                    # flat download, e.g. model_loader.py in root
            hit = [h for h in have if Path(h).name == Path(e).name and h not in EXPECTED]
        (relocate.__setitem__(e, sorted(hit)[0]) if hit else missing.append(e))
    stray = sorted(h for h in have if h not in EXPECTED and not h.startswith("tests/__") and h not in DATA_ONLY
                   and not h.endswith((".db", ".pyc")))
    ok = len(EXPECTED) - len(relocate) - len(missing)
    print(f"\n✅ {ok}/{len(EXPECTED)} expected files are in the right place")
    if relocate:
        print(f"\n📦 {len(relocate)} files exist but in the wrong place:")
        for dst, src in relocate.items():
            print(f"   {src}  →  {dst}")
    if missing:
        print(f"\n❌ {len(missing)} files are missing (re-download the zip and copy them):")
        for m in missing: print("   ", m)
    for d in DATA_ONLY:
        if d not in have:
            print(f"\n⚠️  {d} not found: copy it from your old repo" + (" (or run: python train_models.py)" if d.startswith("models/") else ""))
    if stray:
        print("\n🗑️  Not part of the project (safe to delete after you check them):")
        for s in stray[:25]: print("   ", s)
        if len(stray) > 25: print(f"    … and {len(stray) - 25} more")
    if fix and relocate:
        for dst, src in relocate.items():
            (ROOT / dst).parent.mkdir(parents=True, exist_ok=True)
            if not (ROOT / dst).exists():
                shutil.copy2(ROOT / src, ROOT / dst)
        print(f"\n✔ Copied {len(relocate)} files into place. Originals were left untouched. Run again to re-check.")
    elif relocate:
        print("\nRun  python check_structure.py --fix  to copy them into place.")
    if not (relocate or missing):
        print("\n🎉 Layout is correct. Next: pip install -r requirements.txt && pytest")


if __name__ == "__main__":
    main("--fix" in sys.argv)
