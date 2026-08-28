import os
import json

base_dir = "/home/ivan/Projects/AI_Projects/JurisBot/jurisconsultor/ejemplos_legales"
out_file = os.path.join(base_dir, "templates.json")

template_index = {}

for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith(".docx") and "Magia" not in f and not f.startswith(".~lock"):
            rel_path = os.path.relpath(os.path.join(root, f), base_dir)
            # Create a simple key from filename.
            # Convert to lower, replace spaces and dashes with underscores, remove " muestra" if present
            key = f.lower().replace(".docx", "").replace(" muestra", "").strip().replace(" ", "_").replace("-", "_")
            template_index[key] = {
                "file_path": rel_path,
                "description": f.replace(".docx", "")
            }

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(template_index, f, indent=4, ensure_ascii=False)

print("Created templates.json with", len(template_index), "entries.")
