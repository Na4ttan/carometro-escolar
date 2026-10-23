import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Aluno } from '../../shared/models/aluno.model';

@Injectable({ providedIn: 'root' })
export class AlunoService {
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

    return this.http.get<any>(`${environment.apiUrl}/alunos/`, { params: httpParams }).pipe(
      map(res => (Array.isArray(res) ? res : (res.results ?? [])))
    );
  }

  cadastrar(formData: FormData) {
    return this.http.post<Aluno>(`${environment.apiUrl}/alunos/`, formData);
  }

  atualizar(id: number, dados: Record<string, unknown>) {
    return this.http.patch<Aluno>(`${environment.apiUrl}/alunos/${id}/`, dados);
  }

  arquivar(id: number) {
    return this.http.post<Aluno>(`${environment.apiUrl}/alunos/${id}/arquivar/`, {});
  }

  restaurar(id: number) {
    return this.http.post<Aluno>(`${environment.apiUrl}/alunos/${id}/restaurar/`, {});
  }

  excluir(id: number) {
    return this.http.delete(`${environment.apiUrl}/alunos/${id}/`);
  }
}
