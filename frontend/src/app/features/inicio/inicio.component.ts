import { Component, inject, OnInit, signal } from '@angular/core';
import { AlunoService } from '../../core/services/aluno.service';
import { ProfessorService } from '../../core/services/professor.service';
import { EscolaService } from '../../core/services/escola.service';
import { AuthService } from '../../core/services/auth.service';
import { Aluno } from '../../shared/models/aluno.model';
import { Professor } from '../../shared/models/professor.model';
import { Escola } from '../../shared/models/escola.model';
import { AlunoFormComponent } from '../aluno-form/aluno-form.component';
import { ProfessorFormComponent } from '../professor-form/professor-form.component';

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [AlunoFormComponent, ProfessorFormComponent],
  templateUrl: './inicio.component.html',
  styleUrl: 'inicio.component.css',
})
export class InicioComponent implements OnInit {
  private authService = inject(AuthService);
  private escolaService = inject(EscolaService);
  private alunoService = inject(AlunoService);
  private professorService = inject(ProfessorService);

  perfil = this.authService.perfil;
  escola = signal<Escola | null>(null);
  alunos = signal<Aluno[]>([]);
  professores = signal<Professor[]>([]);
  mensagem = signal('');
  erro = signal('');

  ngOnInit() {
    this.escolaService.buscar().subscribe(e => this.escola.set(e));
    this.carregarAlunos();
    this.carregarProfessores();
  }

  carregarAlunos() {
    this.alunoService.listar().subscribe(lista => this.alunos.set(lista));
  }

  carregarProfessores() {
    this.professorService.listar().subscribe(lista => this.professores.set(lista));
  }

  onAlunoAdicionado(nome: string) {
    this.mensagem.set(`${nome} foi cadastrado(a).`);
    this.carregarAlunos();
  }

  onProfessorAdicionado(nome: string) {
    this.mensagem.set(`${nome} foi cadastrado(a).`);
    this.carregarProfessores();
  }
}