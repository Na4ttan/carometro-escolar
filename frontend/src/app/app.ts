import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { PhotoPickerComponent } from './photo-picker';
import { Escola } from './shared/models/escola.model';
import { UsuarioPerfil } from './shared/models/usuario-perfil.model';
import { Turma } from './shared/models/turma.model';
import { Aluno } from './shared/models/aluno.model';
import { Professor } from './shared/models/professor.model';

type Pagina = 'inicio' | 'consulta';
type TipoConsulta = 'todos' | 'alunos' | 'professores';
type Tema = 'claro' | 'escuro';

@Component({
  selector: 'app-root',
  imports: [FormsModule, PhotoPickerComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  private readonly apiUrl =
    typeof window !== 'undefined' && window.location?.origin
      ? window.location.port === '4200'
        ? `http://${window.location.hostname}:8000/api`
        : `${window.location.origin}/api`
      : 'http://127.0.0.1:8000/api';

  token = signal<string | null>(null);
  perfil = signal<UsuarioPerfil | null>(null);
  escola = signal<Escola | null>(null);
  turmas = signal<Turma[]>([]);
  alunos = signal<Aluno[]>([]);
  professores = signal<Professor[]>([]);
  mensagem = signal('');
  erro = signal('');
  pagina = signal<Pagina>('inicio');
  tema = signal<Tema>('claro');
  consulta = {
    tipo: 'todos' as TipoConsulta,
    termo: '',
    turmaId: '',
  };

  credenciais = { username: '', password: '' };
  alunoForm = {
    nome_completo: '',
    nome_social: '',
    data_nascimento: '',
    matricula: '',
    turma: '',
  };
  alunoFoto: File | null = null;
  professorForm = {
    nome_completo: '',
    email: '',
    senha: '',
    confirmacao_senha: '',
    matricula_funcional: '',
  };
  professorFoto: File | null = null;
  turmasProfessor: number[] = [];

  constructor(private readonly http: HttpClient) {}

  ngOnInit(): void {
    const temaSalvo = localStorage.getItem('carometro_tema');
    if (temaSalvo === 'escuro' || temaSalvo === 'claro') {
      this.aplicarTema(temaSalvo);
    } else {
      this.aplicarTema('claro');
    }

    const token = localStorage.getItem('carometro_token');
    if (token) {
      this.token.set(token);
      this.carregarDados();
    }
  }

  entrar(): void {
    this.erro.set('');
    this.http
      .post<{ token: string; tipo: 'escola' | 'professor'; nome: string }>(
        `${this.apiUrl}/auth/login/`,
        this.credenciais,
      )
      .subscribe({
        next: ({ token }) => {
          localStorage.setItem('carometro_token', token);
          this.token.set(token);
          this.credenciais = { username: '', password: '' };
          this.carregarDados();
        },
        error: (error: HttpErrorResponse) =>
          this.erro.set(this.mensagemErro(error, 'Usuário ou senha inválidos.')),
      });
  }

  sair(): void {
    const headers = this.headers();
    this.http.post(`${this.apiUrl}/auth/logout/`, {}, { headers }).subscribe({
      next: () => this.limparSessao(),
      error: () => this.limparSessao(),
    });
  }

  alternarTema(): void {
    this.aplicarTema(this.tema() === 'claro' ? 'escuro' : 'claro');
  }

  cadastrarAluno(): void {
    this.erro.set('');
    this.mensagem.set('');
    if (!this.alunoFoto) {
      this.erro.set('Selecione ou tire uma foto do aluno.');
      return;
    }

    const payload = new FormData();
    payload.append('nome_completo', this.alunoForm.nome_completo);
    payload.append('turma', this.alunoForm.turma);
    payload.append('foto', this.alunoFoto);
    this.adicionarCampoOpcional(payload, 'nome_social', this.alunoForm.nome_social);
    this.adicionarCampoOpcional(
      payload,
      'data_nascimento',
      this.alunoForm.data_nascimento,
    );
    this.adicionarCampoOpcional(payload, 'matricula', this.alunoForm.matricula);

    this.http
      .post<Aluno>(`${this.apiUrl}/alunos/`, payload, {
        headers: this.headers(),
      })
      .subscribe({
        next: (aluno) => {
          this.alunoForm = {
            nome_completo: '',
            nome_social: '',
            data_nascimento: '',
            matricula: '',
            turma: '',
          };
          this.alunoFoto = null;
          this.mensagem.set(`${aluno.nome_completo} foi cadastrado(a).`);
          this.carregarAlunos();
        },
        error: (error: HttpErrorResponse) =>
          this.erro.set(this.mensagemErro(error, 'Não foi possível cadastrar o aluno.')),
      });
  }

  cadastrarProfessor(): void {
    this.erro.set('');
    this.mensagem.set('');

    if (!this.professorForm.email.trim()) {
      this.erro.set('Informe o e-mail do professor (será seu login de acesso).');
      return;
    }

    if (!this.professorForm.senha || this.professorForm.senha.length < 6) {
      this.erro.set('A senha de acesso do professor deve ter pelo menos 6 caracteres.');
      return;
    }

    if (this.professorForm.senha !== this.professorForm.confirmacao_senha) {
      this.erro.set('A confirmação de senha não confere com a senha informada.');
      return;
    }

    if (!this.professorFoto) {
      this.erro.set('Selecione ou tire uma foto do professor.');
      return;
    }

    if (this.turmasProfessor.length === 0) {
      this.erro.set('Associe o professor a pelo menos uma turma.');
      return;
    }

    const payload = new FormData();
    payload.append('nome_completo', this.professorForm.nome_completo);
    payload.append('email', this.professorForm.email.trim().toLowerCase());
    payload.append('senha', this.professorForm.senha);
    payload.append('confirmacao_senha', this.professorForm.confirmacao_senha);
    payload.append('foto', this.professorFoto);
    this.turmasProfessor.forEach((id) => payload.append('turmas', String(id)));
    this.adicionarCampoOpcional(
      payload,
      'matricula_funcional',
      this.professorForm.matricula_funcional,
    );

    this.http
      .post<Professor>(`${this.apiUrl}/professores/`, payload, {
        headers: this.headers(),
      })
      .subscribe({
        next: (professor) => {
          this.professorForm = {
            nome_completo: '',
            email: '',
            senha: '',
            confirmacao_senha: '',
            matricula_funcional: '',
          };
          this.professorFoto = null;
          this.turmasProfessor = [];
          this.mensagem.set(`${professor.nome_completo} foi cadastrado(a).`);
          this.carregarProfessores();
        },
        error: (error: HttpErrorResponse) =>
          this.erro.set(
            this.mensagemErro(error, 'Não foi possível cadastrar o professor.'),
          ),
      });
  }

  alternarTurmaProfessor(id: number, selecionado: boolean): void {
    this.turmasProfessor = selecionado
      ? [...this.turmasProfessor, id]
      : this.turmasProfessor.filter((turmaId) => turmaId !== id);
  }

  onTurmaProfessorChange(id: number, event: Event): void {
    if (event.target instanceof HTMLInputElement) {
      this.alternarTurmaProfessor(id, event.target.checked);
    }
  }

  navegar(pagina: Pagina): void {
    this.pagina.set(pagina);
    this.erro.set('');
    this.mensagem.set('');
  }

  alunosFiltrados(): Aluno[] {
    const termo = this.consulta.termo.trim().toLocaleLowerCase('pt-BR');
    const turmaId = this.consulta.turmaId ? Number(this.consulta.turmaId) : null;
    return this.alunos().filter((aluno) => {
      const correspondeAoTexto =
        !termo ||
        [
          aluno.nome_completo,
          aluno.nome_social ?? '',
          aluno.matricula ?? '',
          aluno.turma_nome ?? '',
        ].some((valor) => valor.toLocaleLowerCase('pt-BR').includes(termo));
      return correspondeAoTexto && (!turmaId || aluno.turma_id === turmaId);
    });
  }

  professoresFiltrados(): Professor[] {
    if (this.perfil()?.tipo === 'professor') {
      return [];
    }
    const termo = this.consulta.termo.trim().toLocaleLowerCase('pt-BR');
    const turmaId = this.consulta.turmaId ? Number(this.consulta.turmaId) : null;
    return this.professores().filter((professor) => {
      const correspondeAoTexto =
        !termo ||
        [
          professor.nome_completo,
          professor.email ?? '',
          professor.matricula_funcional ?? '',
          ...professor.turmas_nomes,
        ].some((valor) => valor.toLocaleLowerCase('pt-BR').includes(termo));
      return (
        correspondeAoTexto &&
        (!turmaId || professor.turmas_ids.includes(turmaId))
      );
    });
  }

  limparConsulta(): void {
    this.consulta = {
      tipo: this.perfil()?.tipo === 'professor' ? 'alunos' : 'todos',
      termo: '',
      turmaId: '',
    };
  }

  private carregarDados(): void {
    const headers = this.headers();
    this.http.get<UsuarioPerfil>(`${this.apiUrl}/auth/perfil/`, { headers }).subscribe({
      next: (perfil) => {
        this.perfil.set(perfil);
        if (perfil.tipo === 'escola') {
          this.http.get<Escola>(`${this.apiUrl}/escola/`, { headers }).subscribe({
            next: (escola) => this.escola.set(escola),
            error: (error: HttpErrorResponse) => this.tratarFalhaDeAcesso(error),
          });
          this.http.get<Turma[]>(`${this.apiUrl}/turmas/`, { headers }).subscribe({
            next: (turmas) => this.turmas.set(turmas),
            error: (error: HttpErrorResponse) => this.tratarFalhaDeAcesso(error),
          });
          this.carregarAlunos();
          this.carregarProfessores();
        } else if (perfil.tipo === 'professor') {
          this.pagina.set('consulta');
          this.consulta.tipo = 'alunos';
          this.http.get<Turma[]>(`${this.apiUrl}/turmas/`, { headers }).subscribe({
            next: (turmas) => this.turmas.set(turmas),
            error: (error: HttpErrorResponse) => this.tratarFalhaDeAcesso(error),
          });
          this.carregarAlunos();
        }
      },
      error: (error: HttpErrorResponse) => this.tratarFalhaDeAcesso(error),
    });
  }

  private carregarAlunos(): void {
    this.http
      .get<Aluno[]>(`${this.apiUrl}/alunos/`, { headers: this.headers() })
      .subscribe({
        next: (alunos) => this.alunos.set(alunos),
        error: (error: HttpErrorResponse) => this.tratarFalhaDeAcesso(error),
      });
  }

  private carregarProfessores(): void {
    this.http
      .get<Professor[]>(`${this.apiUrl}/professores/`, {
        headers: this.headers(),
      })
      .subscribe({
        next: (professores) => this.professores.set(professores),
        error: (error: HttpErrorResponse) => this.tratarFalhaDeAcesso(error),
      });
  }

  private headers(): HttpHeaders {
    return new HttpHeaders({ Authorization: `Token ${this.token() ?? ''}` });
  }

  private aplicarTema(tema: Tema): void {
    this.tema.set(tema);
    document.documentElement.dataset['theme'] = tema;
    document.body.dataset['theme'] = tema;
    localStorage.setItem('carometro_tema', tema);
  }

  private adicionarCampoOpcional(
    payload: FormData,
    chave: string,
    valor: string,
  ): void {
    if (valor && valor.trim()) {
      payload.append(chave, valor.trim());
    }
  }

  private limparSessao(): void {
    localStorage.removeItem('carometro_token');
    this.token.set(null);
    this.perfil.set(null);
    this.escola.set(null);
    this.turmas.set([]);
    this.alunos.set([]);
    this.professores.set([]);
    this.alunoFoto = null;
    this.professorFoto = null;
    this.pagina.set('inicio');
    this.limparConsulta();
  }

  private tratarFalhaDeAcesso(error: HttpErrorResponse): void {
    if (error.status === 401 || error.status === 403) {
      this.limparSessao();
    }
    this.erro.set(
      this.mensagemErro(error, 'Não foi possível carregar os dados.'),
    );
  }

  private mensagemErro(error: HttpErrorResponse, fallback: string): string {
    if (typeof error.error === 'object' && error.error !== null) {
      const payload = error.error as Record<string, unknown>;
      if (typeof payload['detail'] === 'string') {
        return payload['detail'];
      }
      const mensagens = Object.values(payload)
        .flatMap((valor) => (Array.isArray(valor) ? valor : [valor]))
        .filter((valor): valor is string => typeof valor === 'string');
      if (mensagens.length > 0) {
        return mensagens.join(' ');
      }
    }
    return fallback;
  }
}
