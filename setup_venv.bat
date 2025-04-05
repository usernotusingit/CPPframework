@echo off 
echo Criando ambiente virtual... 
python -m venv venv 
echo Ativando ambiente virtual... 
call venv\Scripts\activate.bat 
echo Instalando dependências... 
pip install -r requirements.txt 
echo. 
echo Configuração concluída 
echo python main.py 
echo. 
echo Ou executar os mocks das LLMs com: 
echo cd mock 
echo python mock_llms.py 
pause 
