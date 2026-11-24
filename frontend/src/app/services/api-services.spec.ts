import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { EntrepriseService } from './entreprise.service';
import { EquipeService } from './equipe.service';
import { ProjetService } from './projet.service';
import { ProjetDetailleService } from './projet-detaille.service';

/**
 * The services call relative /api/... URLs: nginx (Docker, Kubernetes) and
 * proxy.conf.json (ng serve) forward them to the backend. These tests pin the
 * method and URL of every call, so a route change cannot slip through.
 */
describe('API services', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function expectCall(method: string, url: string, body: unknown = null) {
    const req = http.expectOne(url);
    expect(req.request.method).toBe(method);
    if (body !== null) expect(req.request.body).toEqual(body);
    req.flush(method === 'DELETE' ? null : {});
  }

  it('EntrepriseService', () => {
    const s = TestBed.inject(EntrepriseService);
    const e = { id: 1, nom: 'Acme', adresse: 'Tunis' };
    s.getAll().subscribe();      expectCall('GET', '/api/entreprise/all');
    s.getById(1).subscribe();    expectCall('GET', '/api/entreprise/get/1');
    s.add(e).subscribe();        expectCall('POST', '/api/entreprise/add', e);
    s.update(e).subscribe();     expectCall('PUT', '/api/entreprise/update', e);
    s.delete(1).subscribe();     expectCall('DELETE', '/api/entreprise/delete/1');
  });

  it('EquipeService, including the company assignment', () => {
    const s = TestBed.inject(EquipeService);
    const q = { id: 3, nom: 'Data', specialite: 'ETL' };
    s.getAll().subscribe();      expectCall('GET', '/api/equipe/all');
    s.getById(3).subscribe();    expectCall('GET', '/api/equipe/get/3');
    s.add(q).subscribe();        expectCall('POST', '/api/equipe/add', q);
    s.update(q).subscribe();     expectCall('PUT', '/api/equipe/update', q);
    s.delete(3).subscribe();     expectCall('DELETE', '/api/equipe/delete/3');
    s.assignToEntreprise(3, 1).subscribe(); expectCall('PUT', '/api/equipe/assign-entreprise/3/1');
  });

  it('ProjetService', () => {
    const s = TestBed.inject(ProjetService);
    const p = { id: 2, sujet: 'ERP' };
    s.getAll().subscribe();      expectCall('GET', '/api/projet/all');
    s.getById(2).subscribe();    expectCall('GET', '/api/projet/get/2');
    s.add(p).subscribe();        expectCall('POST', '/api/projet/add', p);
    s.update(p).subscribe();     expectCall('PUT', '/api/projet/update', p);
    s.delete(2).subscribe();     expectCall('DELETE', '/api/projet/delete/2');
  });

  it('ProjetDetailleService, including the project assignment', () => {
    const s = TestBed.inject(ProjetDetailleService);
    const d = { id: 4, description: 'API', technologie: 'Angular', coutProvisoire: 5000, dateDebut: '2026-09-01' };
    s.getAll().subscribe();      expectCall('GET', '/api/projet-detaille/all');
    s.getById(4).subscribe();    expectCall('GET', '/api/projet-detaille/get/4');
    s.add(d).subscribe();        expectCall('POST', '/api/projet-detaille/add', d);
    s.update(d).subscribe();     expectCall('PUT', '/api/projet-detaille/update', d);
    s.delete(4).subscribe();     expectCall('DELETE', '/api/projet-detaille/delete/4');
    s.assignToProjet(4, 2).subscribe(); expectCall('PUT', '/api/projet-detaille/assign-projet/4/2');
  });
});
