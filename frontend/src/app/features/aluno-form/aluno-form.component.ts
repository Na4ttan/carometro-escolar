import { Component, inject, OnInit, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
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
  form = {
    nome_completo: '', nome_social: '',
    data_nascimento: '', matricula: '', turma: '',
  };

  ngOnInit() {
    this.turmaService.listar().subscribe(lista => this.turmas.set(lista));
  }

  cadastrar() {
    this.erro.set('');
    if (!this.foto) { this.erro.set('Selecione ou tire uma foto do aluno.'); return; }

    const payload = new FormData();
    payload.append('nome_completo', this.form.nome_completo);
    payload.append('turma', this.form.turma);
    payload.append('foto', this.foto);
    if (this.form.nome_social.trim()) payload.append('nome_social', this.form.nome_social.trim());
    if (this.form.data_nascimento) payload.append('data_nascimento', this.form.data_nascimento);
    if (this.form.matricula.trim()) payload.append('matricula', this.form.matricula.trim());

    this.alunoService.cadastrar(payload).subscribe({
      next: (aluno) => {
        this.alunoAdicionado.emit(aluno.nome_completo);
        this.form = { nome_completo: '', nome_social: '', data_nascimento: '', matricula: '', turma: '' };
        this.foto = null;
      },
      error: () => this.erro.set('Não foi possível cadastrar o aluno.'),
    });
  }
}