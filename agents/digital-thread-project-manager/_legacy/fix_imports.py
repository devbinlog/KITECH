import os
import shutil

src_agent = os.path.abspath("src")
src_iso = os.path.abspath(r"..\..\Digital-Thread\ISO_api\src")

def process_dir(iso_name, agent_name):
    target_dir = os.path.join(src_agent, agent_name)
    source_dir = os.path.join(src_iso, iso_name)
    
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                content = content.replace('from src.entities', 'from src.models.entities')
                content = content.replace('import src.entities', 'import src.models.entities')
                content = content.replace('from src.schemas', 'from src.models.schemas')
                content = content.replace('import src.schemas', 'import src.models.schemas')
                content = content.replace('from src.utils', 'from src.utils')
                
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)

process_dir('entities', 'models/entities')
process_dir('schemas', 'models/schemas')
shutil.copy(os.path.join(src_iso, 'database.py'), os.path.join(src_agent, 'database.py'))

print("Successfully fixed models encodings.")
