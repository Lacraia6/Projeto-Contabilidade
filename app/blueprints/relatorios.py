from flask import Blueprint, render_template, request, jsonify, make_response
from app.models import Empresa, Tarefa, RelacionamentoTarefa, Periodo, Usuario
from app.db import db
from datetime import datetime, timedelta
import json
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')


@bp.get('')
@bp.get('/')
def return_page():
	"""Página principal de relatórios"""
	empresas_opts = [{"id": e.id, "nome": e.nome} for e in Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()]
	return render_template('relatorios.html', aba='relatorios', empresas=empresas_opts)


@bp.get('/api/dados')
def api_dados_relatorio():
	"""API para buscar dados do relatório baseado nos filtros"""
	try:
		# Parâmetros da requisição
		empresa_id = request.args.get('empresa_id', type=int)
		funcionario_id = request.args.get('funcionario_id', type=int)
		tarefa_id = request.args.get('tarefa_id', type=int)
		data_inicial = request.args.get('data_inicial')
		data_final = request.args.get('data_final')
		status = request.args.get('status', 'todos')
		
		# Construir query base
		query = db.session.query(
			Periodo.id,
			Empresa.nome.label('empresa_nome'),
			Tarefa.nome.label('tarefa_nome'),
			Tarefa.tipo.label('tarefa_tipo'),
			Periodo.periodo_label,
			Periodo.status,
			Periodo.data_conclusao,
			Periodo.data_retificacao,
			RelacionamentoTarefa.prazo_especifico,
			Usuario.nome.label('responsavel_nome')
		).join(RelacionamentoTarefa, Periodo.relacionamento_tarefa_id == RelacionamentoTarefa.id)\
		 .join(Empresa, RelacionamentoTarefa.empresa_id == Empresa.id)\
		 .join(Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id)\
		 .outerjoin(Usuario, RelacionamentoTarefa.responsavel_id == Usuario.id)
		
		# Aplicar filtros
		if empresa_id:
			query = query.filter(RelacionamentoTarefa.empresa_id == empresa_id)
		
		if funcionario_id:
			query = query.filter(RelacionamentoTarefa.responsavel_id == funcionario_id)
		
		if tarefa_id:
			query = query.filter(RelacionamentoTarefa.tarefa_id == tarefa_id)
		
		if status != 'todos':
			query = query.filter(Periodo.status == status)
		
		# Aplicar filtros de período
		if data_inicial and data_final:
			from datetime import datetime
			data_inicio = datetime.strptime(data_inicial, '%Y-%m-%d').date()
			data_fim = datetime.strptime(data_final, '%Y-%m-%d').date()
			query = query.filter(Periodo.inicio.between(data_inicio, data_fim))
		
		# Executar query
		resultados = query.order_by(Empresa.nome, Periodo.inicio.desc()).all()
		
		# Converter para dicionários
		dados = []
		for r in resultados:
			# Usar data de retificação se houver, senão usar data de conclusão
			data_final = r.data_retificacao if r.data_retificacao else r.data_conclusao
			label_data = 'Retificação' if r.data_retificacao else 'Conclusão'
			
			dados.append({
				'id': r.id,
				'empresa_nome': r.empresa_nome,
				'tarefa_nome': r.tarefa_nome,
				'tarefa_tipo': r.tarefa_tipo,
				'periodo': r.periodo_label,
				'periodo_formatado': r.periodo_label,
				'status': r.status,
				'status_texto': _get_status_texto(r.status),
				'data_conclusao': data_final.strftime('%d/%m/%Y') if data_final else '',
				'label_data': label_data,
				'prazo_especifico': r.prazo_especifico.strftime('%d/%m/%Y') if r.prazo_especifico else '',
				'responsavel_nome': r.responsavel_nome or 'Não atribuído'
			})
		
		# Calcular estatísticas
		stats = _calcular_estatisticas(dados)
		
		return jsonify({
			'success': True,
			'dados': dados,
			'stats': stats,
			'total_registros': len(dados)
		})
		
	except Exception as e:
		return jsonify({
			'success': False,
			'error': str(e)
		}), 500


@bp.get('/pdf')
def gerar_pdf():
	"""Gerar relatório em PDF"""
	try:
		# Parâmetros da requisição
		empresa_id = request.args.get('empresa_id', type=int)
		funcionario_id = request.args.get('funcionario_id', type=int)
		tarefa_id = request.args.get('tarefa_id', type=int)
		data_inicial = request.args.get('data_inicial')
		data_final = request.args.get('data_final')
		status = request.args.get('status', 'todos')
		
		# Buscar dados
		response = api_dados_relatorio()
		if response[1] != 200:  # Se houve erro
			return response
		
		data = response[0].get_json()
		if not data['success']:
			return jsonify({'error': data['error']}), 500
		
		# Criar PDF
		buffer = io.BytesIO()
		doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
		
		# Estilos
		styles = getSampleStyleSheet()
		title_style = ParagraphStyle(
			'CustomTitle',
			parent=styles['Heading1'],
			fontSize=16,
			spaceAfter=30,
			alignment=TA_CENTER,
			textColor=colors.darkblue
		)
		
		# Conteúdo do PDF
		story = []
		
		# Título
		story.append(Paragraph("Relatório de Tarefas", title_style))
		story.append(Spacer(1, 12))
		
		# Informações do filtro
		filtros_texto = _gerar_texto_filtros(empresa_id, funcionario_id, tarefa_id, data_inicial, data_final, status)
		story.append(Paragraph(f"<b>Filtros aplicados:</b> {filtros_texto}", styles['Normal']))
		story.append(Spacer(1, 12))
		
		# Estatísticas
		stats = data['stats']
		story.append(Paragraph("<b>Resumo:</b>", styles['Heading2']))
		stats_texto = f"""
		• Total de registros: {data['total_registros']}<br/>
		• Pendentes: {stats['pendentes']}<br/>
		• Em andamento: {stats['em_andamento']}<br/>
		• Concluídas: {stats['concluidas']}<br/>
		• Taxa de conclusão: {stats['taxa_conclusao']:.1f}%
		"""
		story.append(Paragraph(stats_texto, styles['Normal']))
		story.append(Spacer(1, 20))
		
		# Tabela de dados
		if data['dados']:
			story.append(Paragraph("<b>Detalhamento:</b>", styles['Heading2']))
			story.append(Spacer(1, 12))
			
			# Cabeçalho da tabela
			headers = ['Empresa', 'Tarefa', 'Tipo', 'Período', 'Status', 'Responsável', 'Conclusão']
			data_table = [headers]
			
			# Dados da tabela
			for item in data['dados']:
				data_table.append([
					item['empresa_nome'],
					item['tarefa_nome'],
					item['tarefa_tipo'],
					item['periodo_formatado'],
					item['status_texto'],
					item['responsavel_nome'],
					item['data_conclusao']
				])
			
			# Criar tabela
			table = Table(data_table, repeatRows=1)
			table.setStyle(TableStyle([
				('BACKGROUND', (0, 0), (-1, 0), colors.grey),
				('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
				('ALIGN', (0, 0), (-1, -1), 'LEFT'),
				('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
				('FONTSIZE', (0, 0), (-1, 0), 10),
				('BOTTOMPADDING', (0, 0), (-1, 0), 12),
				('BACKGROUND', (0, 1), (-1, -1), colors.beige),
				('GRID', (0, 0), (-1, -1), 1, colors.black),
				('FONTSIZE', (0, 1), (-1, -1), 8),
			]))
			
			story.append(table)
		else:
			story.append(Paragraph("Nenhum registro encontrado com os filtros aplicados.", styles['Normal']))
		
		# Rodapé
		story.append(Spacer(1, 20))
		story.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal']))
		
		# Construir PDF
		doc.build(story)
		
		# Preparar resposta
		buffer.seek(0)
		response = make_response(buffer.getvalue())
		response.headers['Content-Type'] = 'application/pdf'
		response.headers['Content-Disposition'] = f'attachment; filename=relatorio_tarefas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
		
		return response
		
	except Exception as e:
		return jsonify({'error': str(e)}), 500


def _calcular_periodo(periodo, ano=None, mes=None):
	"""Calcula período baseado nos parâmetros"""
	hoje = datetime.now()
	
	if periodo == 'ultimoMes':
		data_fim = hoje.replace(day=1) - timedelta(days=1)
		data_inicio = data_fim.replace(day=1)
	elif periodo == 'ultimos3':
		data_fim = hoje
		data_inicio = hoje - timedelta(days=90)
	elif periodo == 'ultimos6':
		data_fim = hoje
		data_inicio = hoje - timedelta(days=180)
	elif periodo == 'ultimoAno':
		data_fim = hoje
		data_inicio = hoje - timedelta(days=365)
	elif periodo == 'anoAtual':
		data_inicio = hoje.replace(month=1, day=1)
		data_fim = hoje
	elif periodo == 'anoAnterior':
		ano_anterior = hoje.year - 1
		data_inicio = hoje.replace(year=ano_anterior, month=1, day=1)
		data_fim = hoje.replace(year=ano_anterior, month=12, day=31)
	elif periodo == 'personalizado':
		if ano:
			if mes:
				data_inicio = datetime(ano, mes, 1)
				if mes == 12:
					data_fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
				else:
					data_fim = datetime(ano, mes + 1, 1) - timedelta(days=1)
			else:
				data_inicio = datetime(ano, 1, 1)
				data_fim = datetime(ano, 12, 31)
		else:
			data_inicio = None
			data_fim = None
	else:
		data_inicio = None
		data_fim = None
	
	return data_inicio, data_fim


def _get_status_texto(status):
	"""Converte status para texto legível"""
	status_map = {
		'pendente': 'Pendente',
		'em_andamento': 'Em Andamento',
		'concluida': 'Concluída',
		'atrasada': 'Atrasada'
	}
	return status_map.get(status, status)


def _calcular_estatisticas(dados):
	"""Calcula estatísticas dos dados"""
	total = len(dados)
	pendentes = len([d for d in dados if d['status'] == 'pendente'])
	em_andamento = len([d for d in dados if d['status'] == 'em_andamento'])
	concluidas = len([d for d in dados if d['status'] == 'concluida'])
	
	taxa_conclusao = (concluidas / total * 100) if total > 0 else 0
	
	return {
		'total': total,
		'pendentes': pendentes,
		'em_andamento': em_andamento,
		'concluidas': concluidas,
		'taxa_conclusao': taxa_conclusao
	}


def _gerar_texto_filtros(empresa_id, funcionario_id, tarefa_id, data_inicial, data_final, status):
	"""Gera texto descritivo dos filtros aplicados"""
	filtros = []
	
	if empresa_id:
		empresa = Empresa.query.get(empresa_id)
		if empresa:
			filtros.append(f"Empresa: {empresa.nome}")
	
	if funcionario_id:
		funcionario = Usuario.query.get(funcionario_id)
		if funcionario:
			filtros.append(f"Funcionário: {funcionario.nome}")
	
	if tarefa_id:
		tarefa = Tarefa.query.get(tarefa_id)
		if tarefa:
			filtros.append(f"Tarefa: {tarefa.nome}")
	
	if data_inicial and data_final:
		from datetime import datetime
		data_ini = datetime.strptime(data_inicial, '%Y-%m-%d').strftime('%d/%m/%Y')
		data_fim = datetime.strptime(data_final, '%Y-%m-%d').strftime('%d/%m/%Y')
		filtros.append(f"Período: {data_ini} a {data_fim}")
	
	if status != 'todos':
		status_texto = {
			'pendente': 'Pendentes',
			'em_andamento': 'Em Andamento',
			'concluida': 'Concluídas'
		}.get(status, status)
		filtros.append(f"Status: {status_texto}")
	
	return ", ".join(filtros) if filtros else "Todos os registros"
