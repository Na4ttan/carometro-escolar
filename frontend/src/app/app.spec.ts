import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    localStorage.removeItem('carometro_token');
    localStorage.removeItem('carometro_tema');
    document.documentElement.removeAttribute('data-theme');
    document.body.removeAttribute('data-theme');
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    })
      .compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render title', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Um jeito simples');
  });

  it('filters students and teachers by search term and selected class', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    app.perfil.set({
      tipo: 'escola',
      id: 1,
      nome: 'Escola Modelo',
    });
    app.alunos.set([
      {
        id: 1,
        nome_completo: 'Ana Silva',
        nome_social: null,
        data_nascimento: null,
        matricula: 'A-10',
        foto: null,
        turma_id: 3,
        turma_nome: '6º A - 2026',
      },
      {
        id: 2,
        nome_completo: 'Bruno Lima',
        nome_social: null,
        data_nascimento: null,
        matricula: 'B-20',
        foto: null,
        turma_id: 4,
        turma_nome: '7º A - 2026',
      },
    ]);
    app.professores.set([
      {
        id: 1,
        nome_completo: 'Carla Souza',
        email: 'carla@example.com',
        matricula_funcional: 'P-30',
        foto: null,
        turmas_ids: [3],
        turmas_nomes: ['6º A - 2026'],
      },
    ]);
    app.consulta = { tipo: 'todos', termo: 'a-10', turmaId: '3' };

    expect(app.alunosFiltrados().map((aluno) => aluno.nome_completo)).toEqual([
      'Ana Silva',
    ]);
    expect(
      app.professoresFiltrados().map((professor) => professor.nome_completo),
    ).toEqual([]);

    app.consulta = { tipo: 'todos', termo: 'carla', turmaId: '3' };
    expect(
      app.professoresFiltrados().map((professor) => professor.nome_completo),
    ).toEqual(['Carla Souza']);
  });

  it('hides professors list for teacher profile and filters assigned students', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    app.perfil.set({
      tipo: 'professor',
      id: 10,
      nome: 'Professor João',
      email: 'joao@escola.com',
      escola_nome: 'Escola Modelo',
    });
    app.alunos.set([
      {
        id: 1,
        nome_completo: 'Ana Silva',
        nome_social: null,
        data_nascimento: null,
        matricula: 'A-10',
        foto: null,
        turma_id: 3,
        turma_nome: '6º A - 2026',
      },
    ]);
    app.professores.set([
      {
        id: 1,
        nome_completo: 'Carla Souza',
        email: 'carla@example.com',
        matricula_funcional: 'P-30',
        foto: null,
        turmas_ids: [3],
        turmas_nomes: ['6º A - 2026'],
      },
    ]);

    expect(app.professoresFiltrados()).toEqual([]);
    expect(app.alunosFiltrados().length).toBe(1);
  });

  it('validates email, password and password confirmation when registering a teacher', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;

    app.professorForm = {
      nome_completo: 'Professor Teste',
      email: '',
      senha: '',
      confirmacao_senha: '',
      matricula_funcional: '',
    };
    app.cadastrarProfessor();
    expect(app.erro()).toContain('Informe o e-mail do professor');

    app.professorForm.email = 'prof@teste.com';
    app.professorForm.senha = '123';
    app.cadastrarProfessor();
    expect(app.erro()).toContain('A senha de acesso do professor deve ter pelo menos 6 caracteres');

    app.professorForm.senha = 'senha123';
    app.professorForm.confirmacao_senha = 'outrasenha';
    app.cadastrarProfessor();
    expect(app.erro()).toContain('A confirmação de senha não confere');
  });

  it('toggles the global theme and persists the selected preference', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.theme-toggle')).toBeTruthy();

    expect(document.documentElement.dataset['theme']).toBe('claro');

    app.alternarTema();
    expect(app.tema()).toBe('escuro');
    expect(document.documentElement.dataset['theme']).toBe('escuro');
    expect(document.body.dataset['theme']).toBe('escuro');
    expect(localStorage.getItem('carometro_tema')).toBe('escuro');

    const restoredFixture = TestBed.createComponent(App);
    restoredFixture.detectChanges();
    expect(restoredFixture.componentInstance.tema()).toBe('escuro');

    app.alternarTema();
    expect(app.tema()).toBe('claro');
    expect(document.body.dataset['theme']).toBe('claro');
    expect(localStorage.getItem('carometro_tema')).toBe('claro');
  });
});
