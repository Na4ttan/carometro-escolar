import { Component, inject, OnInit, output, signal } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { TurmaService } from '../../core/services/turma.service';
import { AlunoService } from '../../core/services/aluno.service';
import { Turma } from '../../shared/models/turma.model';
import { PhotoPickerComponent } from '../../shared/components/photo-picker/photo-picker.component';

@Component({
  selector: 'app-aluno-form',
  standalone: true,
  imports: [FormsModule, PhotoPickerComponent],
  templateUrl: './aluno-form.component.html',
  styleUrl: './aluno-form.component.css',
})
export class AlunoFormComponent implements OnInit {
  private turmaService = inject(TurmaService);
  private alunoService = inject(AlunoService);

  readonly alunoAdicionado = output<string>();

  turmas = signal<Turma[]>([]);
  foto: File | null = null;
  erro = signal('');
  erroImportacao = signal('');
  resultadoImportacao = signal('');
  importando = signal(false);
  nivelEnsinoImportacao = signal<'fundamental' | 'medio' | ''>('');
  form = {
    nome_completo: '', nome_social: '',
    data_nascimento: '', matricula: '', turma: '',
  };

  ngOnInit() {
    this.turmaService.listar().subscribe(lista => this.turmas.set(lista));
  }

  cadastrar(cadastroForm?: NgForm) {
    this.erro.set('');
    const matricula = this.form.matricula.trim();
    if (!matricula) {
      this.erro.set('Informe a matrícula do aluno.');
      return;
    }

    const payload = new FormData();
    payload.append('nome_completo', this.form.nome_completo);
    payload.append('turma', this.form.turma);
    if (this.foto) payload.append('foto', this.foto);
    if (this.form.nome_social.trim()) payload.append('nome_social', this.form.nome_social.trim());
    if (this.form.data_nascimento) payload.append('data_nascimento', this.form.data_nascimento);
    payload.append('matricula', matricula);

    this.alunoService.cadastrar(payload).subscribe({
      next: (aluno) => {
        this.form = { nome_completo: '', nome_social: '', data_nascimento: '', matricula: '', turma: '' };
        this.foto = null;
        cadastroForm?.resetForm(this.form);
        this.alunoAdicionado.emit(aluno.nome_completo);
      },
      error: () => this.erro.set('Não foi possível cadastrar o aluno.'),
    });
  }

  importarCsv(event: Event) {
    const input = event.target as HTMLInputElement;
    const arquivo = input.files?.[0];
    const nivelEnsino = this.nivelEnsinoImportacao();
    this.erroImportacao.set('');
    this.resultadoImportacao.set('');
    if (!arquivo) return;
    if (!nivelEnsino) {
      this.erroImportacao.set('Selecione o nível de ensino antes de importar.');
      input.value = '';
      return;
    }
    if (!arquivo.name.toLowerCase().endsWith('.csv')) {
      this.erroImportacao.set('Selecione um arquivo CSV.');
      input.value = '';
      return;
    }

    this.importando.set(true);
    this.alunoService.importarCsv(arquivo, nivelEnsino).subscribe({
      next: (resultado) => {
        const status = resultado.erros.length ? 'Importação finalizada com erros' : 'Importação concluída';
        this.resultadoImportacao.set(
          `${status}: ${resultado.criados} aluno(s) cadastrado(s) e ${resultado.atualizados} atualizado(s).`,
        );
        if (resultado.erros.length) {
          this.erroImportacao.set(resultado.erros
            .map(item => `Linha ${item.linha}: ${item.mensagem}`)
            .join(' '));
        }
        this.importando.set(false);
        input.value = '';
      },
      error: (resposta) => {
        this.erroImportacao.set(resposta.error?.detail ?? 'Não foi possível importar o CSV.');
        this.importando.set(false);
        input.value = '';
      },
    });
  }
}
