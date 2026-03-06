#!/bin/bash

echo "🚨 Resolvendo Git Merge Conflict..."
echo ""

# Opção 1: Abortar o merge
echo "Opção 1: Abortar o merge atual"
echo "Comando: git merge --abort"
echo ""

read -p "Deseja abortar o merge? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    git merge --abort
    echo "✅ Merge abortado"
else
    echo "Cancelado"
    exit 1
fi

echo ""
echo "Verificando status..."
git status

echo ""
echo "✨ Pronto! Status limpo"
echo ""
echo "Agora você pode fazer novo commit:"
echo "  git add ."
echo "  git commit -m \"Initial commit\""

