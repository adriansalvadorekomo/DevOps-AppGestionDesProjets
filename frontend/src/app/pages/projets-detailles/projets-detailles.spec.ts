import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { ProjetsDetaillesComponent } from './projets-detailles';
import { ProjetDetailleService } from '../../services/projet-detaille.service';
import { ProjetService } from '../../services/projet.service';

describe('ProjetsDetaillesComponent', () => {
  const detail = { id: 4, description: 'API', technologie: 'Spring Boot', coutProvisoire: 12000,
                   dateDebut: '2026-09-01', projet: { id: 2 } };
  const service = {
    getAll: vi.fn(() => of([detail])),
    add: vi.fn(() => of(detail)),
    update: vi.fn(() => of(detail)),
    delete: vi.fn(() => of(undefined)),
  };
  const projets = { getAll: vi.fn(() => of([{ id: 2, sujet: 'ERP' }])) };
  let page: ProjetsDetaillesComponent;

  beforeEach(async () => {
    vi.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [ProjetsDetaillesComponent],
      providers: [
        { provide: ProjetDetailleService, useValue: service },
        { provide: ProjetService, useValue: projets },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ProjetsDetaillesComponent);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads the details and the projects for the selector', () => {
    expect(page.projetsDetailles()).toEqual([detail]);
    expect(page.projets()).toHaveLength(1);
  });

  it('adds a detail linked to the selected project', () => {
    page.openAdd();
    page.update('technologie', 'Angular');
    page.update('coutProvisoire', 5000);
    page.selectedProjetId.set(2);
    page.save();
    expect(service.add).toHaveBeenCalledWith({
      description: '', technologie: 'Angular', coutProvisoire: 5000, dateDebut: '', projet: { id: 2 },
    });
    expect(page.showForm()).toBe(false);
  });

  it('edits with update; a cleared project is sent as none', () => {
    page.edit(detail);
    expect(page.selectedProjetId()).toBe(2);
    page.selectedProjetId.set(null);
    page.save();
    expect(service.update).toHaveBeenCalledWith({ ...detail, projet: undefined });
  });

  it('deletes only after confirmation', () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true);
    page.delete(4);
    page.delete(4);
    expect(service.delete).toHaveBeenCalledTimes(1);
    confirm.mockRestore();
  });
});
