from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Tabelas principais
class Setor(db.Model):
    __tablename__ = 'setor'
    id_setor = db.Column(db.Integer, primary_key=True)
    nome_setor = db.Column(db.String(150))
    projars = db.relationship('Projar', backref='setor', lazy=True)

class Local(db.Model):
    __tablename__ = 'local'
    id_local = db.Column(db.Integer, primary_key=True)
    nome_local = db.Column(db.String(150))
    projars = db.relationship('Projar', backref='local', lazy=True)

class Projar(db.Model):
    __tablename__ = 'projar'
    id_projar = db.Column(db.Integer, primary_key=True)
    n_chamada_projar = db.Column(db.String(10))
    titulo_projar = db.Column(db.String(500))
    local_id = db.Column(db.Integer, db.ForeignKey('local.id_local'))
    data_projar = db.Column(db.Date)
    colacao_projar = db.Column(db.String(20))
    conteudo_projar = db.Column(db.String(1000))
    notas_gerais_projar = db.Column(db.String(1000))
    setor_id = db.Column(db.Integer, db.ForeignKey('setor.id_setor'))
    fonte_projar = db.Column(db.String(200))
    escala_projar = db.Column(db.String(20))
    outras_versoes_projar = db.Column(db.String(96))
    
    # Relacionamentos muitos-para-muitos
    assuntos = db.relationship('Assunto', secondary='projar_assunto', backref='projars')
    executores = db.relationship('Executor', secondary='projar_executor', backref='projars')
    areas_geograficas = db.relationship('AreaGeografica', secondary='projar_area_geografica', backref='projars')
    autores = db.relationship('Autor', secondary='projar_autor', backref='projars')

# Tabelas auxiliares
class Assunto(db.Model):
    __tablename__ = 'assunto'
    id_assunto = db.Column(db.Integer, primary_key=True)
    nome_assunto = db.Column(db.String(300))

class Executor(db.Model):
    __tablename__ = 'executor'
    id_executor = db.Column(db.Integer, primary_key=True)
    nome_executor = db.Column(db.String(200))
    tipo_executor = db.Column(db.String(40))

class AreaGeografica(db.Model):
    __tablename__ = 'area_geografica'
    id_area_geografica = db.Column(db.Integer, primary_key=True)
    nome_area_geografica = db.Column(db.String(150))

class Autor(db.Model):
    __tablename__ = 'autor'
    id_autor = db.Column(db.Integer, primary_key=True)
    nome_autor = db.Column(db.String(200))
    tipo_autor = db.Column(db.String(30))  # "primario", "secundario corporativo", "secundario evento"

# Tabelas de junção
class ProjarAssunto(db.Model):
    __tablename__ = 'projar_assunto'
    id_projar_assunto = db.Column(db.Integer, primary_key=True)
    projar_id = db.Column(db.Integer, db.ForeignKey('projar.id_projar'))
    assunto_id = db.Column(db.Integer, db.ForeignKey('assunto.id_assunto'))

class ProjarExecutor(db.Model):
    __tablename__ = 'projar_executor'
    id_projar_executor = db.Column(db.Integer, primary_key=True)
    projar_id = db.Column(db.Integer, db.ForeignKey('projar.id_projar'))
    executor_id = db.Column(db.Integer, db.ForeignKey('executor.id_executor'))

class ProjarAreaGeografica(db.Model):
    __tablename__ = 'projar_area_geografica'
    id_projar_area_geografica = db.Column(db.Integer, primary_key=True)
    projar_id = db.Column(db.Integer, db.ForeignKey('projar.id_projar'))
    area_geografica_id = db.Column(db.Integer, db.ForeignKey('area_geografica.id_area_geografica'))

class ProjarAutor(db.Model):
    __tablename__ = 'projar_autor'
    id_projar_autor = db.Column(db.Integer, primary_key=True)
    projar_id = db.Column(db.Integer, db.ForeignKey('projar.id_projar'))
    autor_id = db.Column(db.Integer, db.ForeignKey('autor.id_autor'))