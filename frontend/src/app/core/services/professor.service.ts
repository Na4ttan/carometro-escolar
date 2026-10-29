import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Professor } from '../../shared/models/professor.model';

@Injectable({ providedIn: 'root' })
export class ProfessorService {
  private http = inject(HttpClient);

  listar(params?: {
    search?: string;
    turma_id?: number | string;
    ano_letivo?: number | string;
    incluir_arquivados?: boolean;
    page?: number;
    page_size?: number;
    sem_paginacao?: boolean;
  }) {
    let httpParams = new HttpParams();
    if (params?.search) httpParams = httpParams.set('search', params.search);
    if (params?.turma_id) httpParams = httpParams.set('turma', params.turma_id.toString());
    if (params?.ano_letivo) httpParams = httpParams.set('ano_letivo', params.ano_letivo.toString());
    if (params?.incluir_arquivados) httpParams = httpParams.set('incluir_arquivados', 'true');
    if (params?.page) httpParams = httpParams.set('page', params.page.toString());
    if (params?.page_size) httpParams = httpParams.set('page_size', params.page_size.toString());
    if (params?.sem_paginacao) httpParams = httpParams.set('sem_paginacao', 'true');

    return this.http.get<any>(`${environment.apiUrl}/professores/`, { params: httpParams }).pipe(
      map(res => (Array.isArray(res) ? res : (res.results ?? [])))
    );
  }

  cadastrar(formData: FormData) {
    return this.http.post<Professor>(`${environment.apiUrl}/professores/`, formData);
  }

  atualizar(id: number, dados: Record<string, unknown>) {
    return this.http.patch<Professor>(`${environment.apiUrl}/professores/${id}/`, dados);
  }

  buscar(id: number) {
    return this.http.get<Professor>(`${environment.apiUrl}/professores/${id}/`);
  }

  arquivar(id: number) {
    return this.http.post<Professor>(`${environment.apiUrl}/professores/${id}/arquivar/`, {});
  }

  restaurar(id: number) {
    return this.http.post<Professor>(`${environment.apiUrl}/professores/${id}/restaurar/`, {});
  }

  excluir(id: number) {
    return this.http.delete(`${environment.apiUrl}/professores/${id}/`);
  }
}
