import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AlunoService } from '../../core/services/aluno.service';
import { ProfessorService } from '../../core/services/professor.service';
import { TurmaService } from '../../core/services/turma.service';
import { Aluno } from '../../shared/models/aluno.model';
import { Professor } from '../../shared/models/professor.model';
import { Turma } from '../../shared/models/turma.model';
import { AuthService } from '../../core/services/auth.service';

type TipoConsulta = 'todos' | 'alunos' | 'professores';

@Component({
  selector: 'app-consulta',
  standalone: true,
  templateUrl: './consulta.component.html',
  imports: [FormsModule],
  providers: [AlunoService, ProfessorService, TurmaService, AuthService]
})
export class ConsultaComponent implements OnInit {
  private alunoService = inject(AlunoService);
  private professorService = inject(ProfessorService);
  private turmaService = inject(TurmaService);
  private authService = inject(AuthService);

  perfil = this.authService.perfil;
  tipoConsulta = signal<TipoConsulta>('todos');
  alunos = signal<Aluno[]>([]);
  professores = signal<Professor[]>([]);
  turmas = signal<Turma[]>([]);
  filtro = signal('');
  turmaId = signal('');

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
    this.alunoService.listar().subscribe(lista => this.alunos.set(lista));
    this.professorService.listar().subscribe(lista => this.professores.set(lista));
    this.turmaService.listar().subscribe(lista => this.turmas.set(lista));
  }

  limparFiltros(): void {
    this.filtro.set('');
    this.turmaId.set('');
    this.tipoConsulta.set(this.perfil()?.tipo === 'professor' ? 'alunos' : 'todos');
  }
}
