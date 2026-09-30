import { Component, inject, OnInit, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TurmaService } from '../../core/services/turma.service';
import { ProfessorService } from '../../core/services/professor.service';
import { Turma } from '../../shared/models/turma.model';
import { PhotoPickerComponent } from '../../shared/components/photo-picker/photo-picker.component';

@Component({
  selector: 'app-professor-form',
  standalone: true,
  imports: [FormsModule, PhotoPickerComponent],
  templateUrl: 'professor-form.component.html',
  styleUrls: ['professor-form.component.css'],
})
export class ProfessorFormComponent implements OnInit {
  private turmaService = inject(TurmaService);
  private professorService = inject(ProfessorService);

  readonly professorAdicionado = output<string>();

  turmas = signal<Turma[]>([]);
  foto: File | null = null;
  turmasSelecionadas: number[] = [];
  erro = signal('');
  form = {
    nome_completo: '', email: '',
    senha: '', confirmacao_senha: '', matricula_funcional: '',
  };

  ngOnInit() {
    this.turmaService.listar().subscribe(lista => this.turmas.set(lista));
  }

  onTurmaChange(id: number, event: Event) {
    if (!(event.target instanceof HTMLInputElement)) return;
    this.turmasSelecionadas = event.target.checked
      ? [...this.turmasSelecionadas, id]
      : this.turmasSelecionadas.filter(t => t !== id);
  }

  cadastrar() {
    this.erro.set('');
    if (!this.form.email.trim()) { this.erro.set('Informe o e-mail do professor.'); return; }
    if (this.form.senha.length < 6) { this.erro.set('A senha deve ter pelo menos 6 caracteres.'); return; }
    if (this.form.senha !== this.form.confirmacao_senha) { this.erro.set('A confirmação de senha não confere.'); return; }
    if (!this.foto) { this.erro.set('Selecione ou tire uma foto do professor.'); return; }
    if (this.turmasSelecionadas.length === 0) { this.erro.set('Associe o professor a pelo menos uma turma.'); return; }

    const payload = new FormData();
    payload.append('nome_completo', this.form.nome_completo);
    payload.append('email', this.form.email.trim().toLowerCase());
    payload.append('senha', this.form.senha);
    payload.append('confirmacao_senha', this.form.confirmacao_senha);
    payload.append('foto', this.foto);
    this.turmasSelecionadas.forEach(id => payload.append('turmas', String(id)));
    if (this.form.matricula_funcional.trim()) payload.append('matricula_funcional', this.form.matricula_funcional.trim());

    this.professorService.cadastrar(payload).subscribe({
      next: (professor) => {
        this.professorAdicionado.emit(professor.nome_completo);
        this.form = { nome_completo: '', email: '', senha: '', confirmacao_senha: '', matricula_funcional: '' };
        this.foto = null;
        this.turmasSelecionadas = [];
      },
      error: () => this.erro.set('Não foi possível cadastrar o professor.'),
    });
  }
}