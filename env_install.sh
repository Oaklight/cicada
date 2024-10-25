# setup MiniGPT-3D
cd MiniGPT-3D

# Use mamba if present, otherwise use conda
if command -v mamba &>/dev/null; then
    mamba env create -f environment.yml
else
    conda env create -f environment.yml
fi

conda activate minigpt_3d
bash env_install.sh

cd ..
# download MiniGPT-3D weight from huggingface or hf-mirror.com
# more on how to use hf-mirror.com: https://hf-mirror.com
./tools/hfd.sh YuanTang96/MiniGPT-3D --tool aria2c -x 16 --local-dir ./MiniGPT-3D --exclude config.json --exclude README.md --exclude .gitattributes
