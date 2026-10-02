import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Aluno } from '../../shared/models/aluno.model';

@Injectable({ providedIn: 'root' })
export class AlunoService {
  private http = inject(HttpClient);

  listar() {
    return this.http.get<Aluno[]>(`${environment.apiUrl}/alunos/`);
  }

  cadastrar(formData: FormData) {
    return this.http.post<Aluno>(`${environment.apiUrl}/alunos/`, formData);
  }
}