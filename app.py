import re
from flask import Flask, render_template, request, jsonify
from config import Config
from models import ProjarAssunto, ProjarAutor, db, Projar, Setor, Local, Assunto, Executor, Autor, AreaGeografica
from datetime import datetime
from sqlalchemy import or_, extract

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
    """Página inicial"""
    try:
        total_projetos = Projar.query.count()
    except Exception:
        total_projetos = 0
    
    return render_template('index.html', total_projetos=total_projetos)

@app.route('/projetos', methods=['GET', 'POST'])
def listar_projetos():
    """Lista projetos com filtros"""
    projetos = Projar.query
    
    # Aplicar filtros
    filtros = {}
    
    # Filtro por ID
    if 'id_projar' in request.args and request.args['id_projar']:
        try:
            id_val = int(request.args['id_projar'])
            projetos = projetos.filter(Projar.id_projar == id_val)
            filtros['id_projar'] = request.args['id_projar']
        except ValueError:
            pass
    
    # Filtro por Número de Chamada
    if 'n_chamada' in request.args and request.args['n_chamada']:
        projetos = projetos.filter(Projar.n_chamada_projar.like(f"%{request.args['n_chamada']}%"))
        filtros['n_chamada'] = request.args['n_chamada']
    
    # Filtro por Autor
    if 'autor_id' in request.args and request.args['autor_id']:
        try:
            autor_id_int = int(request.args['autor_id'])
            autor_tipo = request.args.get('autor_tipo', 'todos')
            
            # Sempre usar subquery para evitar duplicação
            subquery = db.session.query(ProjarAutor.projar_id).filter(
                ProjarAutor.autor_id == autor_id_int
            )
            
            # Se for filtrar por tipo específico
            if autor_tipo != 'todos':
                # JOIN para garantir que o autor tenha o tipo correto
                subquery = subquery.join(
                    Autor, ProjarAutor.autor_id == Autor.id_autor
                ).filter(Autor.tipo_autor == autor_tipo)
            
            # Aplicar o filtro
            projetos = projetos.filter(Projar.id_projar.in_(subquery))
            
            filtros['autor_id'] = request.args['autor_id']
            if autor_tipo != 'todos':
                filtros['autor_tipo'] = autor_tipo
                
        except ValueError:
            pass
    
    # Filtro por Local
    if 'local_id' in request.args and request.args['local_id']:
        try:
            local_id_int = int(request.args['local_id'])
            projetos = projetos.filter(Projar.local_id == local_id_int)
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
                    extract('month', Projar.data_projar) == mes_int,
                    extract('year', Projar.data_projar) == ano_int
                )
                filtros['mes'] = mes
                filtros['ano'] = ano
            else:
                # Apenas mês
                projetos = projetos.filter(extract('month', Projar.data_projar) == mes_int)
                filtros['mes'] = mes
    
    # Filtro por Conteúdo
    if 'conteudo' in request.args and request.args['conteudo']:
        conteudo = request.args['conteudo']
        projetos = projetos.filter(Projar.conteudo_projar.like(f"%{conteudo}%"))
        filtros['conteudo'] = conteudo
    
    # Filtro por Executor
    if 'executor_id' in request.args and request.args['executor_id']:
        try:
            executor_id_int = int(request.args['executor_id'])
            projetos = projetos.join(Projar.executores).filter(Executor.id_executor == executor_id_int)
            filtros['executor_id'] = request.args['executor_id']
        except ValueError:
            pass
    
     # Filtro por Assunto Inteligente
    if 'assunto' in request.args and request.args['assunto']:
        assunto_busca = request.args['assunto'].strip()
        if assunto_busca:
            print(f"\n🔍 BUSCA EM ASSUNTO: '{assunto_busca}'")
            
            # FUNÇÃO REPETIDA (igual à do título)
            def criar_padrao_regex_assunto(palavra):
                """Cria padrão regex onde vogais podem ter acentos"""
                padrao = ''
                for letra in palavra:
                    letra_lower = letra.lower()
                    if letra_lower == 'a':
                        padrao += '[aáàãâä]'
                    elif letra_lower == 'e':
                        padrao += '[eéèêë]'
                    elif letra_lower == 'i':
                        padrao += '[iíìîï]'
                    elif letra_lower == 'o':
                        padrao += '[oóòõôö]'
                    elif letra_lower == 'u':
                        padrao += '[uúùûü]'
                    elif letra_lower == 'c':
                        padrao += '[cç]'
                    else:
                        padrao += re.escape(letra)
                return padrao
            
            # Para cada palavra na busca, criar padrão
            palavras = assunto_busca.split()
            condicoes_assunto = []
            
            for palavra in palavras:
                if len(palavra) >= 2:
                    # Padrão case-insensitive com acentos
                    padrao_regex = criar_padrao_regex_assunto(palavra)
                    
                    # Subquery: projetos que têm assuntos com essa palavra
                    subquery = db.session.query(ProjarAssunto.projar_id)\
                        .join(Assunto, ProjarAssunto.assunto_id == Assunto.id_assunto)
                    
                    # Aplicar regex ou LIKE no nome do assunto
                    try:
                        # Usar regex do PostgreSQL (case-insensitive, aceita acentos)
                        subquery = subquery.filter(Assunto.nome_assunto.op('~*')(padrao_regex))
                        print(f"   ✅ Assunto regex: '{palavra}' → '{padrao_regex}'")
                    except Exception as e:
                        # Fallback: usar LIKE tradicional
                        print(f"   ⚠️  Regex falhou para '{palavra}', usando LIKE")
                        subquery = subquery.filter(Assunto.nome_assunto.ilike(f"%{palavra}%"))
                    
                    # Adicionar condição: projeto deve estar na subquery
                    condicoes_assunto.append(Projar.id_projar.in_(subquery))
                else:
                    # Se palavra tem menos de 2 caracteres, usar LIKE simples
                    print(f"   ℹ️  Palavra muito curta '{palavra}' (<2 chars), usando LIKE")
                    subquery = db.session.query(ProjarAssunto.projar_id)\
                        .join(Assunto, ProjarAssunto.assunto_id == Assunto.id_assunto)\
                        .filter(Assunto.nome_assunto.ilike(f"%{palavra}%"))
                    condicoes_assunto.append(Projar.id_projar.in_(subquery))
            
            # Aplicar condições AND (todas palavras devem aparecer nos assuntos)
            if condicoes_assunto:
                projetos = projetos.filter(*condicoes_assunto)
                print(f"   📊 Filtro aplicado: {len(condicoes_assunto)} condição(ões)")
            
            filtros['assunto'] = assunto_busca
    
    # Filtro por Setor
    if 'setor_id' in request.args and request.args['setor_id']:
        try:
            setor_id_int = int(request.args['setor_id'])
            projetos = projetos.filter(Projar.setor_id == setor_id_int)
            filtros['setor_id'] = request.args['setor_id']
        except ValueError:
            pass
        
    # Filtro por Título
    if 'titulo' in request.args and request.args['titulo']:
        titulo_busca = request.args['titulo'].strip()
        if titulo_busca:
            # Método: buscar de forma "aproximada"
            def criar_padrao_regex(palavra):
                """Cria padrão regex onde vogais podem ter acentos"""
                padrao = ''
                for letra in palavra:
                    letra_lower = letra.lower()
                    if letra_lower == 'a':
                        padrao += '[aáàãâä]'
                    elif letra_lower == 'e':
                        padrao += '[eéèêë]'
                    elif letra_lower == 'i':
                        padrao += '[iíìîï]'
                    elif letra_lower == 'o':
                        padrao += '[oóòõôö]'
                    elif letra_lower == 'u':
                        padrao += '[uúùûü]'
                    elif letra_lower == 'c':
                        padrao += '[cç]'
                    else:
                        padrao += re.escape(letra)
                return padrao
            
            # Para cada palavra na busca, criar padrão
            palavras = titulo_busca.split()
            condicoes = []
            
            for palavra in palavras:
                if len(palavra) >= 2:
                    # Padrão case-insensitive com acentos
                    padrao_regex = criar_padrao_regex(palavra)
                    
                    # Usar regex do PostgreSQL se disponível
                    try:
                        condicoes.append(Projar.titulo_projar.op('~*')(padrao_regex))
                    except:
                        # Fallback: usar LIKE tradicional
                        condicoes.append(Projar.titulo_projar.ilike(f"%{palavra}%"))
            
            # Aplicar condições AND (todas palavras devem aparecer)
            if condicoes:
                projetos = projetos.filter(*condicoes)
            
            filtros['titulo'] = titulo_busca
    
    # Buscar dados para os selects
    locais = Local.query.order_by(Local.nome_local).all()
    setores = Setor.query.order_by(Setor.nome_setor).all()
    assuntos = Assunto.query.order_by(Assunto.nome_assunto).all()
    executores = Executor.query.order_by(Executor.nome_executor).all()
    autores = Autor.query.order_by(Autor.nome_autor).all()
    
    # Buscar conteúdos distintos
    conteudos = db.session.query(Projar.conteudo_projar).distinct().filter(Projar.conteudo_projar.isnot(None)).all()
    conteudos = [c[0] for c in conteudos if c[0]]
    
    projetos = projetos.order_by(Projar.id_projar.desc()).all()
            
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
    """API para buscar autores"""
    autores = Autor.query.order_by(Autor.nome_autor).all()
    return jsonify([{
        'id': a.id_autor,
        'nome': a.nome_autor,
        'tipo': a.tipo_autor
    } for a in autores])

@app.route('/api/conteudos')
def get_conteudos():
    """API para buscar conteúdos distintos"""
    conteudos = db.session.query(Projar.conteudo_projar).distinct().filter(Projar.conteudo_projar.isnot(None)).all()
    return jsonify([c[0] for c in conteudos if c[0]])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)