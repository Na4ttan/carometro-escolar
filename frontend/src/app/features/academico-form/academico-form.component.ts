import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { AnoLetivo, TurmaService } from '../../core/services/turma.service';
import { Turma } from '../../shared/models/turma.model';

@Component({
  selector: 'app-academico-form',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './academico-form.component.html',
  styleUrl: './academico-form.component.css',
})
export class AcademicoFormComponent implements OnInit {
  private turmaService = inject(TurmaService);

  anosLetivos = signal<AnoLetivo[]>([]);
  turmas = signal<Turma[]>([]);
  anoSelecionado = signal('');
  anoVigenteId = signal('');
  ativandoAno = signal(false);
  erroAtivarAno = signal('');
  erroAno = signal('');
  erroTurma = signal('');
  sucesso = signal('');
  incluirArquivadas = signal(false);
  turmaEmEdicao = signal<Turma | null>(null);
  salvandoEdicao = signal(false);

  anoForm = { ano: new Date().getFullYear(), data_inicio: '', data_fim: '', ativo: true };
  turmaForm = { ano_letivo: '', nivel_ensino: 'fundamental' as 'fundamental' | 'medio', serie: '', nome: '', turno: 'manha', sala: '' };

  seriesDisponiveis(): number[] {
    return Array.from(
      { length: this.turmaForm.nivel_ensino === 'fundamental' ? 9 : 3 },
      (_, index) => index + 1,
    );
  }

  anoSelecionadoLabel(): number | string {
    const anoSelecionado = this.anosLetivos().find(
      ano => String(ano.id) === this.anoSelecionado(),
    );
    return anoSelecionado?.ano ?? '';
  }

  alterarNivel(nivel: 'fundamental' | 'medio'): void {
    this.turmaForm.nivel_ensino = nivel;
    if (Number(this.turmaForm.serie) > this.seriesDisponiveis().length) {
      this.turmaForm.serie = '';
    }
  }

  ngOnInit(): void {
    this.carregarAnos();
  }

  carregarAnos(): void {
    this.turmaService.listarAnosLetivos().subscribe({
      next: anos => {
        this.anosLetivos.set(anos);
        const vigente = anos.find(ano => ano.ativo);
        this.anoVigenteId.set(vigente ? String(vigente.id) : '');
        if (!this.anoSelecionado() && anos.length) {
          const anoAtivo = vigente ?? anos[0];
          this.selecionarAno(String(anoAtivo.id));
        }
      },
      error: () => this.erroAno.set('Não foi possível carregar os anos letivos.'),
    });
  }

  definirAnoVigente(id: string): void {
    if (!id || this.ativandoAno()) return;
    const anoAnterior = this.anoVigenteId();
    this.anoVigenteId.set(id);
    this.ativandoAno.set(true);
    this.erroAtivarAno.set('');
    this.turmaService.ativarAnoLetivo(Number(id)).subscribe({
      next: anoAtivo => {
        this.anosLetivos.set(this.anosLetivos().map(ano => ({
          ...ano,
          ativo: ano.id === anoAtivo.id,
        })));
        this.anoVigenteId.set(String(anoAtivo.id));
        this.ativandoAno.set(false);
        this.selecionarAno(String(anoAtivo.id));
        this.sucesso.set(`Ano letivo ${anoAtivo.ano} definido como vigente.`);
      },
      error: () => {
        this.anoVigenteId.set(anoAnterior);
        this.ativandoAno.set(false);
        this.erroAtivarAno.set('Não foi possível ativar este ano letivo. Tente novamente.');
      },
    });
  }

  selecionarAno(id: string): void {
    this.anoSelecionado.set(id);
    this.turmaForm.ano_letivo = id;
    if (!id) {
      this.turmas.set([]);
      return;
    }
    this.turmaService.listarTurmasDoAno(Number(id), this.incluirArquivadas()).subscribe({
      next: turmas => this.turmas.set(turmas),
      error: () => this.erroTurma.set('Não foi possível carregar as turmas deste ano.'),
    });
  }

  cadastrarAno(form: NgForm): void {
    this.erroAno.set('');
    this.sucesso.set('');
    this.turmaService.cadastrarAnoLetivo({
      ...this.anoForm,
      data_inicio: this.anoForm.data_inicio || null,
      data_fim: this.anoForm.data_fim || null,
    }).subscribe({
      next: ano => {
        this.anosLetivos.set([ano, ...this.anosLetivos().filter(item => item.id !== ano.id).map(item => ({
          ...item,
          ativo: ano.ativo ? false : item.ativo,
        }))]
          .sort((a, b) => b.ano - a.ano));
        if (ano.ativo) this.anoVigenteId.set(String(ano.id));
        this.anoForm = { ano: new Date().getFullYear(), data_inicio: '', data_fim: '', ativo: true };
        form.resetForm(this.anoForm);
        this.sucesso.set(`Ano letivo ${ano.ano} cadastrado.`);
        this.selecionarAno(String(ano.id));
      },
      error: () => this.erroAno.set('Não foi possível cadastrar o ano letivo. Verifique se ele já existe.'),
    });
  }

  cadastrarTurma(form: NgForm): void {
    this.erroTurma.set('');
    this.sucesso.set('');
    this.turmaService.cadastrarTurma({
      ...this.turmaForm,
      ano_letivo: Number(this.turmaForm.ano_letivo),
      serie: Number(this.turmaForm.serie),
    }).subscribe({
      next: turma => {
        const anoLetivo = this.turmaForm.ano_letivo;
        this.turmaForm = { ano_letivo: anoLetivo, nivel_ensino: 'fundamental', serie: '', nome: '', turno: 'manha', sala: '' };
        form.resetForm(this.turmaForm);
        this.sucesso.set(`Turma ${turma.nome} cadastrada.`);
        this.selecionarAno(anoLetivo);
      },
      error: error => this.erroTurma.set(this.mensagemErroTurma(error)),
    });
  }

  alternarArquivadas(valor: boolean): void {
    this.incluirArquivadas.set(valor);
    if (this.anoSelecionado()) this.selecionarAno(this.anoSelecionado());
  }

  editarTurma(turma: Turma): void {
    this.turmaEmEdicao.set(turma);
    this.turmaForm = {
      ano_letivo: String(this.anosLetivos().find(ano => ano.ano === turma.ano)?.id ?? ''),
      nivel_ensino: turma.nivel_ensino,
      serie: String(turma.serie),
      nome: turma.nome,
      turno: turma.turno,
      sala: turma.sala ?? '',
    };
    this.erroTurma.set('');
  }

  salvarEdicaoTurma(): void {
    const turma = this.turmaEmEdicao();
    if (!turma || this.salvandoEdicao()) return;
    this.salvandoEdicao.set(true);
    this.turmaService.atualizarTurma(turma.id, {
      ...this.turmaForm,
      ano_letivo: Number(this.turmaForm.ano_letivo),
      serie: Number(this.turmaForm.serie),
    }).subscribe({
      next: () => {
        const nome = this.turmaForm.nome;
        this.turmaEmEdicao.set(null);
        this.salvandoEdicao.set(false);
        this.selecionarAno(this.anoSelecionado());
        this.sucesso.set(`Turma ${nome} atualizada.`);
      },
      error: error => {
        this.erroTurma.set(this.mensagemErroTurma(error));
        this.salvandoEdicao.set(false);
      },
    });
  }

  fecharEdicaoTurma(): void {
    this.turmaEmEdicao.set(null);
    this.erroTurma.set('');
  }

  arquivarTurma(turma: Turma): void {
    if (!window.confirm(`Arquivar a turma ${turma.serie}ª ${turma.nome}? As matrículas e os vínculos docentes serão preservados, mas a turma deixará de aparecer nos cadastros ativos.`)) return;
    this.turmaService.arquivarTurma(turma.id).subscribe({
      next: () => { this.fecharEdicaoTurma(); this.selecionarAno(this.anoSelecionado()); },
      error: () => this.erroTurma.set('Não foi possível arquivar esta turma.'),
    });
  }

  restaurarTurma(turma: Turma): void {
    this.turmaService.restaurarTurma(turma.id).subscribe({
      next: () => { this.fecharEdicaoTurma(); this.selecionarAno(this.anoSelecionado()); },
      error: () => this.erroTurma.set('Não foi possível restaurar esta turma.'),
    });
  }

  excluirTurma(turma: Turma): void {
    if (!window.confirm(`Excluir permanentemente a turma ${turma.serie}ª ${turma.nome}? Todas as matrículas e atribuições de professores dessa turma serão apagadas. Esta ação não pode ser desfeita.`)) return;
    this.turmaService.excluirTurma(turma.id).subscribe({
      next: () => { this.fecharEdicaoTurma(); this.selecionarAno(this.anoSelecionado()); },
      error: () => this.erroTurma.set('Não foi possível excluir esta turma.'),
    });
  }

  private mensagemErroTurma(error: unknown): string {
    const fallback = 'Não foi possível cadastrar a turma. Revise os dados e tente novamente.';
    if (!(error instanceof HttpErrorResponse) || error.status >= 500) return fallback;

    const corpo = error.error as Record<string, unknown> | string | null;
    if (typeof corpo === 'string') return corpo || fallback;
    if (!corpo || typeof corpo !== 'object') return fallback;
    if (typeof corpo['detail'] === 'string') return corpo['detail'];

    const mensagens = Object.values(corpo).flatMap(valor => Array.isArray(valor) ? valor : [valor]);
    const textos = mensagens.filter((valor): valor is string => typeof valor === 'string');
    return textos.join(' ') || fallback;
  }
}
