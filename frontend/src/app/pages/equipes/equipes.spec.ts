import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { EquipesComponent } from './equipes';
import { EquipeService } from '../../services/equipe.service';
import { EntrepriseService } from '../../services/entreprise.service';

describe('EquipesComponent', () => {
  const team = { id: 3, nom: 'Data', specialite: 'ETL', entreprise: { id: 1, nom: 'Acme' } };
  const service = {
    getAll: vi.fn(() => of([team])),
    add: vi.fn(() => of(team)),
    update: vi.fn(() => of(team)),
    delete: vi.fn(() => of(undefined)),
  };
  const entreprises = { getAll: vi.fn(() => of([{ id: 1, nom: 'Acme', adresse: 'Tunis' }])) };
  let page: EquipesComponent;

  beforeEach(async () => {
    vi.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [EquipesComponent],
      providers: [
        { provide: EquipeService, useValue: service },
        { provide: EntrepriseService, useValue: entreprises },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(EquipesComponent);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads teams and the companies for the selector', () => {
    expect(page.equipes()).toEqual([team]);
    expect(page.entreprises()).toHaveLength(1);
  });

  it('sends the selected company as a reference, or none', () => {
    page.openAdd();
    page.update('nom', 'Ops');
    page.save();
    expect(service.add).toHaveBeenLastCalledWith({ nom: 'Ops', specialite: '', entreprise: undefined });

    page.openAdd();
    page.selectedEntrepriseId.set(1);
    page.save();
    expect(service.add).toHaveBeenLastCalledWith({ nom: '', specialite: '', entreprise: { id: 1 } });
  });

  it('editing preselects the team company and saves with update', () => {
    page.edit(team);
    expect(page.selectedEntrepriseId()).toBe(1);
    page.save();
    expect(service.update).toHaveBeenCalledWith({ ...team, entreprise: { id: 1 } });
  });

  it('deletes only after confirmation', () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    page.delete(3);
    expect(service.delete).not.toHaveBeenCalled();
    confirm.mockReturnValue(true);
    page.delete(3);
    expect(service.delete).toHaveBeenCalledWith(3);
    page.cancel();
    expect(page.showForm()).toBe(false);
    confirm.mockRestore();
  });
});
