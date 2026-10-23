import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin, of, Subject } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AlunoService } from '../../core/services/aluno.service';
import { ProfessorService } from '../../core/services/professor.service';
import { TurmaService } from '../../core/services/turma.service';
import { Aluno } from '../../shared/models/aluno.model';
import { Professor } from '../../shared/models/professor.model';
import { Turma } from '../../shared/models/turma.model';
import { AuthService } from '../../core/services/auth.service';
import { AnoLetivo } from '../../core/services/turma.service';

type TipoConsulta = 'todos' | 'alunos' | 'professores';

interface AlunoEdicao {
  nome_completo: string;
  nome_social: string;
  data_nascimento: string;
  matricula: string;
  turma: string;
}

interface ProfessorEdicao {
  nome_completo: string;
  email: string;
  matricula_funcional: string;
}

@Component({
  selector: 'app-consulta',
  standalone: true,
  templateUrl: './consulta.component.html',
  styleUrl: './consulta.component.css',
  imports: [FormsModule]
})
export class ConsultaComponent implements OnInit {
  private alunoService = inject(AlunoService);
  private professorService = inject(ProfessorService);
  private turmaService = inject(TurmaService);
  private authService = inject(AuthService);
  private destroyRef = inject(DestroyRef);
  private anoSelecionado$ = new Subject<number>();

  perfil = this.authService.perfil;
  tipoConsulta = signal<TipoConsulta>('todos');
  alunos = signal<Aluno[]>([]);
  professores = signal<Professor[]>([]);
  turmas = signal<Turma[]>([]);
  anosLetivos = signal<AnoLetivo[]>([]);
  anoLetivoId = signal('');
  filtro = signal('');
  turmaId = signal('');
  incluirArquivados = signal(false);
  alunoEmEdicao = signal<Aluno | null>(null);
  professorEmEdicao = signal<Professor | null>(null);
  alunoEdicao: AlunoEdicao = this.novaEdicaoAluno();
  professorEdicao: ProfessorEdicao = this.novaEdicaoProfessor();
  erroEdicao = signal('');
  salvandoEdicao = signal(false);
  turmasDisponiveisEdicao = signal<Turma[]>([]);
  turmasSelecionadasEdicao = signal<number[]>([]);

  alunosFiltrados = computed(() => {
    const termo = this.filtro().trim().toLocaleLowerCase('pt-BR');
    const turmaId = this.turmaId() ? Number(this.turmaId()) : null;
    return this.alunos().filter(a => {
      const correspondeTexto = !termo || [
        a.nome_completo,
        a.nome_social ?? '',
        a.matricula ?? '',
      ].some(v => v.toLocaleLowerCase('pt-BR').includes(termo));
      return correspondeTexto && (!turmaId || a.turma_id === turmaId);
    });
  });

  professoresFiltrados = computed(() => {
    const termo = this.filtro().trim().toLocaleLowerCase('pt-BR');
    const turmaId = this.turmaId() ? Number(this.turmaId()) : null;
    return this.professores().filter(p => {
      const correspondeTexto = !termo || [p.nome_completo, p.email ?? '']
        .some(v => v.toLocaleLowerCase('pt-BR').includes(termo));
      return correspondeTexto && (!turmaId || p.turmas_ids.includes(turmaId));
    });
  });

  turmasFiltradas = computed(() => {
    const termo = this.filtro().trim().toLocaleLowerCase('pt-BR');
    return this.turmas().filter(t =>
      !termo || t.nome.toLocaleLowerCase('pt-BR').includes(termo)
    );
  });

  ngOnInit() {
    this.anoSelecionado$.pipe(
      switchMap(anoLetivo => forkJoin({
        alunos: this.alunoService.listar({ ano_letivo: anoLetivo, sem_paginacao: true, incluir_arquivados: this.incluirArquivados() }),
        professores: this.perfil()?.tipo === 'escola'
          ? this.professorService.listar({ ano_letivo: anoLetivo, sem_paginacao: true, incluir_arquivados: this.incluirArquivados() })
          : of([]),
        turmas: this.turmaService.listarTurmasDoAno(anoLetivo, this.incluirArquivados()),
      })),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(({ alunos, professores, turmas }) => {
      this.alunos.set(alunos);
      this.professores.set(professores);
      this.turmas.set(turmas);
    });

    const perfil = this.perfil();
    const perfil$ = perfil ? of(perfil) : this.authService.carregarPerfil();
    perfil$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(perfil => {
      this.authService.perfil.set(perfil);
      this.turmaService.listarAnosLetivos().subscribe(anos => {
        this.anosLetivos.set(anos);
        const vigente = anos.find(ano => ano.ativo);
        if (vigente) {
          this.selecionarAnoLetivo(String(vigente.id));
        } else if (perfil.tipo === 'professor') {
          this.alunoService.listar().subscribe(lista => this.alunos.set(lista));
          this.turmaService.listar().subscribe(lista => this.turmas.set(lista));
          this.professores.set([]);
        }
      });
    });
  }

  selecionarAnoLetivo(id: string): void {
    this.anoLetivoId.set(id);
    this.turmaId.set('');
    if (id) {
      this.anoSelecionado$.next(Number(id));
    } else {
      this.alunos.set([]);
      this.professores.set([]);
      this.turmas.set([]);
    }
  }

  limparFiltros(): void {
    this.filtro.set('');
    this.turmaId.set('');
    this.tipoConsulta.set(this.perfil()?.tipo === 'professor' ? 'alunos' : 'todos');
  }

  alternarArquivados(valor: boolean): void {
    this.incluirArquivados.set(valor);
    if (this.anoLetivoId()) this.anoSelecionado$.next(Number(this.anoLetivoId()));
  }

  editarAluno(aluno: Aluno): void {
    this.alunoEmEdicao.set(aluno);
    this.alunoEdicao = {
      nome_completo: aluno.nome_completo,
      nome_social: aluno.nome_social ?? '',
      data_nascimento: aluno.data_nascimento ?? '',
      matricula: aluno.matricula ?? '',
      turma: aluno.turma_id ? String(aluno.turma_id) : '',
    };
    this.erroEdicao.set('');
  }

  salvarAluno(): void {
    const aluno = this.alunoEmEdicao();
    if (!aluno || this.salvandoEdicao()) return;
    this.salvandoEdicao.set(true);
    this.erroEdicao.set('');
    this.alunoService.atualizar(aluno.id, {
      nome_completo: this.alunoEdicao.nome_completo,
      nome_social: this.alunoEdicao.nome_social || null,
      data_nascimento: this.alunoEdicao.data_nascimento || null,
      matricula: this.alunoEdicao.matricula || null,
      turma: Number(this.alunoEdicao.turma),
    }).subscribe({
      next: () => { this.alunoEmEdicao.set(null); this.salvandoEdicao.set(false); this.recarregarConsulta(); },
      error: () => { this.erroEdicao.set('Não foi possível salvar. Confira os dados e tente novamente.'); this.salvandoEdicao.set(false); },
    });
  }

  editarProfessor(professor: Professor): void {
    this.professorEmEdicao.set(professor);
    this.professorEdicao = {
      nome_completo: professor.nome_completo,
      email: professor.email ?? '',
      matricula_funcional: professor.matricula_funcional ?? '',
    };
    this.erroEdicao.set('');
    this.turmasDisponiveisEdicao.set([]);
    this.turmasSelecionadasEdicao.set([]);
    this.professorService.buscar(professor.id).subscribe(detalhe => {
      this.turmaService.listarAnosLetivos().subscribe(anos => {
        if (!anos.length) return;
        forkJoin(anos.map(ano => this.turmaService.listarTurmasDoAno(ano.id, true))).subscribe(listas => {
          const disponiveis = listas.flat().filter(turma => turma.ativo);
          this.turmasDisponiveisEdicao.set(disponiveis);
          this.turmasSelecionadasEdicao.set(detalhe.turmas_ids.filter(id => disponiveis.some(turma => turma.id === id)));
        });
      });
    });
  }

  alternarTurmaProfessor(turmaId: number, evento: Event): void {
    const selecionadas = new Set(this.turmasSelecionadasEdicao());
    if ((evento.target as HTMLInputElement).checked) selecionadas.add(turmaId);
    else selecionadas.delete(turmaId);
    this.turmasSelecionadasEdicao.set([...selecionadas]);
  }

  salvarProfessor(): void {
    const professor = this.professorEmEdicao();
    if (!professor || this.salvandoEdicao()) return;
    this.salvandoEdicao.set(true);
    this.erroEdicao.set('');
    this.professorService.atualizar(professor.id, {
      nome_completo: this.professorEdicao.nome_completo,
      email: this.professorEdicao.email,
      matricula_funcional: this.professorEdicao.matricula_funcional || null,
      ...(this.turmasSelecionadasEdicao().length ? { turmas: this.turmasSelecionadasEdicao() } : {}),
    }).subscribe({
      next: () => { this.professorEmEdicao.set(null); this.salvandoEdicao.set(false); this.recarregarConsulta(); },
      error: () => { this.erroEdicao.set('Não foi possível salvar. Confira os dados e tente novamente.'); this.salvandoEdicao.set(false); },
    });
  }

  arquivarAluno(aluno: Aluno): void {
    if (!window.confirm(`Arquivar ${aluno.nome_completo}? O cadastro e as matrículas serão preservados e poderão ser restaurados.`)) return;
    this.alunoService.arquivar(aluno.id).subscribe({
      next: () => { this.fecharEdicao(); this.recarregarConsulta(); },
      error: () => this.erroEdicao.set('Não foi possível arquivar este aluno.'),
    });
  }

  excluirAluno(aluno: Aluno): void {
    if (!window.confirm(`Excluir permanentemente ${aluno.nome_completo}? Todas as matrículas desse aluno também serão apagadas. Esta ação não pode ser desfeita.`)) return;
    this.alunoService.excluir(aluno.id).subscribe({
      next: () => { this.fecharEdicao(); this.recarregarConsulta(); },
      error: () => this.erroEdicao.set('Não foi possível excluir este aluno.'),
    });
  }

  restaurarAluno(aluno: Aluno): void {
    this.alunoService.restaurar(aluno.id).subscribe({
      next: () => { this.fecharEdicao(); this.recarregarConsulta(); },
      error: () => this.erroEdicao.set('Não foi possível restaurar este aluno.'),
    });
  }

  arquivarProfessor(professor: Professor): void {
    if (!window.confirm(`Arquivar ${professor.nome_completo}? O acesso ao Carômetro será desativado, mas os vínculos serão preservados.`)) return;
    this.professorService.arquivar(professor.id).subscribe({
      next: () => { this.fecharEdicao(); this.recarregarConsulta(); },
      error: () => this.erroEdicao.set('Não foi possível arquivar este professor.'),
    });
  }

  excluirProfessor(professor: Professor): void {
    if (!window.confirm(`Excluir permanentemente ${professor.nome_completo}? O cadastro e o acesso de login serão removidos. Esta ação não pode ser desfeita.`)) return;
    this.professorService.excluir(professor.id).subscribe({
      next: () => { this.fecharEdicao(); this.recarregarConsulta(); },
      error: () => this.erroEdicao.set('Não foi possível excluir este professor.'),
    });
  }

  restaurarProfessor(professor: Professor): void {
    this.professorService.restaurar(professor.id).subscribe({
      next: () => { this.fecharEdicao(); this.recarregarConsulta(); },
      error: () => this.erroEdicao.set('Não foi possível restaurar este professor.'),
    });
  }

  fecharEdicao(): void {
    this.alunoEmEdicao.set(null);
    this.professorEmEdicao.set(null);
  }

  private recarregarConsulta(): void {
    if (this.anoLetivoId()) this.anoSelecionado$.next(Number(this.anoLetivoId()));
  }

  private novaEdicaoAluno(): AlunoEdicao {
    return { nome_completo: '', nome_social: '', data_nascimento: '', matricula: '', turma: '' };
  }

  private novaEdicaoProfessor(): ProfessorEdicao {
    return { nome_completo: '', email: '', matricula_funcional: '' };
  }
}
