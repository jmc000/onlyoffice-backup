# Set up guide

### 1. Create and enter scripts dir
```bash
mkdir -p $HOME/scripts
cd $HOME/scripts
```

### 2. Copy repository
```bash
git clone <your-repo>
```

### 3. Set .env
Rename `.env.example` to `.env`:
```bash
cd onlyoffice-backup
mv .env.example .env
```
Then set your docspace url and api key:
```bash
nano .env
```

### 4. Set config.yaml
To create and edit the `config.yaml` run:
```bash
nano config.yaml
```

You can set a list of files to backup:
```yaml
#config.yaml
files:
  - /home/USER/foo/bar.docx
  - /home/USER/toto.docx
```

Or the files within a specific directory:
```yaml
#config.yaml
dirs:
  - /home/USER/Documents/
```
**Note:** 
- `dirs` allow backing up documents (`.docx`, `.xlsx`, `.pptx`) at the root of the directories of the list. 
- it means for example above, `/home/USER/Documents/journal.xlsx` will be backup, but not `/home/USER/Documents/todo.txt` nor `/home/USER/Documents/work/doc.docx`

Or both:
```yaml
#config.yaml
files:
  - /home/USER/foo/bar.docx
  - /home/USER/toto.docx

dirs:
  - /home/USER/Documents/
```

Note:
- {".docx", ".xlsx", ".pptx"}

**Notes:**
- if `files` or `dirs` aren't use, just

### 5. Set python environment
```bash
python -m venv venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -q -r requirements.txt
```

### 6. Configure the daily script
```bash
chmod +x daily.sh
sudo ./daily.sh
```
