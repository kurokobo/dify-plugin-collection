import os
import re
import yaml

def find_readme():
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    readme_path = os.path.join(parent_dir, 'README.md')
    if os.path.isfile(readme_path):
        return readme_path
    raise FileNotFoundError("README.md not found in parent directory.")

def parse_manifest(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return {
        'name': data.get('name', ''),
        'label': data.get('label', {}).get('en_US', ''),
        'description': data.get('description', {}).get('en_US', ''),
        'version': data.get('version', ''),
    }

def collect_manifests(dir_name):
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    target_dir = os.path.join(parent_dir, dir_name)
    if not os.path.isdir(target_dir):
        return []
    manifests = []
    for entry in os.listdir(target_dir):
        subdir = os.path.join(target_dir, entry)
        print(f"  -> Finding manifest for plugin: {subdir}")
        manifest_path = os.path.join(subdir, 'manifest.yaml')
        if os.path.isdir(subdir) and os.path.isfile(manifest_path):
            info = parse_manifest(manifest_path)
            print(f"     -> {info['name']} ({info['version']})")
            manifests.append((entry, info))
    return manifests

def format_manifest_list(root, manifests):
    lines = []
    for dirname, info in sorted(manifests):
        lines.append(f"- [📁 {info['label']} v{info['version']} ({root}/{dirname})](/{root}/{dirname})")
        lines.append(f"  - {info['description']}")
    return '\n'.join(lines)

def update_readme():
    readme_path = find_readme()
    print(f"Repository README.md found at: {readme_path}")
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # <!-- ls: ... --> ... <!-- /ls: ... -->
    pattern = re.compile(
        r'(<!--\s*ls:\s*(\w+)\s*-->\s*)\n*(.*?)\n*(\s*<!--\s*/ls:\s*\2\s*-->)',
        re.DOTALL
    )

    def replacer(match):
        dir_name = match.group(2)
        print(f"Collecting plugin manifests for directory: {dir_name}")
        manifests = collect_manifests(dir_name)
        md_list = format_manifest_list(dir_name, manifests)
        return f"{match.group(1)}{md_list}\n{match.group(4)}"

    new_content = pattern.sub(replacer, content)

    if new_content != content:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("README.md updated.")
    else:
        print("No changes made to README.md.")

if __name__ == "__main__":
    update_readme()
