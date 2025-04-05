@echo off 
call venv\Scripts\activate.bat 
echo Iniciando os mocks das LLMs na porta 8001... 
cd mock 
python mock_llms.py 
