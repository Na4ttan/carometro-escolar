import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Professor } from '../../shared/models/professor.model';

@Injectable({ providedIn: 'root' })
export class ProfessorService {
  private http = inject(HttpClient);

  listar() {
    return this.http.get<Professor[]>(`${environment.apiUrl}/professores/`);
  }

  cadastrar(formData: FormData) {
    return this.http.post<Professor>(`${environment.apiUrl}/professores/`, formData);
  }
}