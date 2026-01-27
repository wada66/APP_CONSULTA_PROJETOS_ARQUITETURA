from flask import Flask, render_template, request, jsonify
from config import Config
from models import ProjenAutor, db, Projen, Setor, Local, Assunto, Executor, Autor, AreaGeografica
from datetime import datetime
from sqlalchemy import or_, extract
from datetime import datetime  # ← Esta importação já deve existir

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
    """Página inicial minimalista"""
    # Passar o contador de projetos para o template
    try:
        total_projetos = Projen.query.count()
    except Exception:
        total_projetos = 0  # Se ainda não houver tabelas
    
    return render_template('index.html', total_projetos=total_projetos)

@app.route('/projetos', methods=['GET', 'POST'])
@app.route('/projetos', methods=['GET', 'POST'])
def listar_projetos():
    """Lista projetos com filtros"""
    projetos = Projen.query
    
    # Aplicar filtros
    filtros = {}
    
    # Filtro por ID
    if 'id_projen' in request.args and request.args['id_projen']:
        try:
            id_val = int(request.args['id_projen'])
            projetos = projetos.filter(Projen.id_projen == id_val)
            filtros['id_projen'] = request.args['id_projen']
        except ValueError:
            pass
    
    # Filtro por Número de Chamada
    if 'n_chamada' in request.args and request.args['n_chamada']:
        projetos = projetos.filter(Projen.n_chamada_projen.like(f"%{request.args['n_chamada']}%"))
        filtros['n_chamada'] = request.args['n_chamada']
    
    # Filtro por Autor - VERSÃO 100% FUNCIONAL
    if 'autor_id' in request.args and request.args['autor_id']:
        try:
            autor_id_int = int(request.args['autor_id'])
            autor_tipo = request.args.get('autor_tipo', 'todos')
            
            print(f"\n🎯 FILTRO AUTOR ATIVADO")
            print(f"   Autor ID: {autor_id_int}")
            print(f"   Tipo solicitado: '{autor_tipo}'")
            
            # DEBUG: Verificar o autor
            autor = Autor.query.get(autor_id_int)
            if autor:
                print(f"   Autor encontrado: {autor.nome_autor}")
                print(f"   Tipo deste autor: '{autor.tipo_autor}'")
            
            # IMPORTANTE: Quando fazemos JOIN, estamos trazendo TODOS os autores do projeto
            # Se um projeto tem 3 autores, o JOIN cria 3 linhas
            # Precisamos de uma abordagem diferente
            
            if autor_tipo == 'todos':
                # Método SIMPLES e FUNCIONAL: subquery
                subquery = db.session.query(ProjenAutor.projen_id).filter(
                    ProjenAutor.autor_id == autor_id_int
                )
                projetos = projetos.filter(Projen.id_projen.in_(subquery))
                print(f"   ✅ Buscando TODOS projetos do autor {autor_id_int}")
                
            else:
                # Método CORRETO para filtrar por tipo
                # 1. Primeiro, pega todos projetos do autor
                # 2. Depois filtra pelos que o autor tem o tipo específico
                
                # Verificar se este autor TEM o tipo solicitado
                autor_com_tipo = Autor.query.filter(
                    Autor.id_autor == autor_id_int,
                    Autor.tipo_autor == autor_tipo
                ).first()
                
                if autor_com_tipo:
                    # Autor existe e tem este tipo, buscar seus projetos
                    subquery = db.session.query(ProjenAutor.projen_id).filter(
                        ProjenAutor.autor_id == autor_id_int
                    )
                    projetos = projetos.filter(Projen.id_projen.in_(subquery))
                    print(f"   ✅ Autor {autor_id_int} é '{autor_tipo}', buscando seus projetos")
                else:
                    # Autor não tem este tipo, não retorna nada
                    print(f"   ⚠️  Autor {autor_id_int} não é '{autor_tipo}', retornando vazio")
                    projetos = projetos.filter(False)  # Força resultado vazio
            
            filtros['autor_id'] = request.args['autor_id']
            filtros['autor_tipo'] = autor_tipo
            
            print(f"   📊 Query final montada")
            
        except ValueError as e:
            print(f"   ❌ Erro no ID do autor: {e}")
            pass
    
    # Filtro por Local
    if 'local_id' in request.args and request.args['local_id']:
        try:
            local_id_int = int(request.args['local_id'])
            projetos = projetos.filter(Projen.local_id == local_id_int)
            filtros['local_id'] = request.args['local_id']
        except ValueError:
            pass
    
    # Filtro por Data (mês/ano)
    if 'mes' in request.args and request.args['mes']:
        mes = request.args['mes']
        ano = request.args.get('ano', '')
        if mes.isdigit():
            mes_int = int(mes)
            if ano.isdigit():
                ano_int = int(ano)
                projetos = projetos.filter(
                    extract('month', Projen.data_projen) == mes_int,
                    extract('year', Projen.data_projen) == ano_int
                )
                filtros['mes'] = mes
                filtros['ano'] = ano
            else:
                # Apenas mês
                projetos = projetos.filter(extract('month', Projen.data_projen) == mes_int)
                filtros['mes'] = mes
    
    # Filtro por Conteúdo
    if 'conteudo' in request.args and request.args['conteudo']:
        conteudo = request.args['conteudo']
        projetos = projetos.filter(Projen.conteudo_projen.like(f"%{conteudo}%"))
        filtros['conteudo'] = conteudo
    
    # Filtro por Executor
    if 'executor_id' in request.args and request.args['executor_id']:
        try:
            executor_id_int = int(request.args['executor_id'])
            projetos = projetos.join(Projen.executores).filter(Executor.id_executor == executor_id_int)
            filtros['executor_id'] = request.args['executor_id']
        except ValueError:
            pass
    
    # Filtro por Assunto
    if 'assunto_id' in request.args and request.args['assunto_id']:
        try:
            assunto_id_int = int(request.args['assunto_id'])
            projetos = projetos.join(Projen.assuntos).filter(Assunto.id_assunto == assunto_id_int)
            filtros['assunto_id'] = request.args['assunto_id']
        except ValueError:
            pass
    
    # Filtro por Setor
    if 'setor_id' in request.args and request.args['setor_id']:
        try:
            setor_id_int = int(request.args['setor_id'])
            projetos = projetos.filter(Projen.setor_id == setor_id_int)
            filtros['setor_id'] = request.args['setor_id']
        except ValueError:
            pass
        
        # Filtro por Título do Projeto (NOVO!)
    if 'titulo' in request.args and request.args['titulo']:
        titulo = request.args['titulo'].strip()
        if titulo:  # Só aplica se não estiver vazio
            # Busca por LIKE (contém) no título
            projetos = projetos.filter(Projen.titulo_projen.like(f"%{titulo}%"))
            filtros['titulo'] = titulo
            print(f"🔍 Buscando por título contendo: '{titulo}'")
    
    # Buscar dados para os selects
    locais = Local.query.order_by(Local.nome_local).all()
    setores = Setor.query.order_by(Setor.nome_setor).all()
    assuntos = Assunto.query.order_by(Assunto.nome_assunto).all()
    executores = Executor.query.order_by(Executor.nome_executor).all()
    autores = Autor.query.order_by(Autor.nome_autor).all()
    
    # Buscar conteúdos distintos
    conteudos = db.session.query(Projen.conteudo_projen).distinct().filter(Projen.conteudo_projen.isnot(None)).all()
    conteudos = [c[0] for c in conteudos if c[0]]
    
    projetos = projetos.order_by(Projen.id_projen.desc()).all()
    
    return render_template('projetos.html',
                         projetos=projetos,
                         locais=locais,
                         setores=setores,
                         assuntos=assuntos,
                         executores=executores,
                         autores=autores,
                         conteudos=conteudos,
                         filtros=filtros,
                         datetime=datetime)

@app.route('/api/autores')
def get_autores():
    """API para buscar autores (usado para select2 ou similar)"""
    autores = Autor.query.order_by(Autor.nome_autor).all()
    return jsonify([{
        'id': a.id_autor,
        'nome': a.nome_autor,
        'tipo': a.tipo_autor
    } for a in autores])

@app.route('/api/conteudos')
def get_conteudos():
    """API para buscar conteúdos distintos"""
    conteudos = db.session.query(Projen.conteudo_projen).distinct().filter(Projen.conteudo_projen.isnot(None)).all()
    return jsonify([c[0] for c in conteudos if c[0]])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)