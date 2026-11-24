import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { EntreprisesComponent } from './entreprises';
import { EntrepriseService } from '../../services/entreprise.service';

describe('EntreprisesComponent', () => {
  const acme = { id: 1, nom: 'Acme', adresse: 'Tunis' };
  const service = {
    getAll: vi.fn(() => of([acme])),
    add: vi.fn(() => of(acme)),
    update: vi.fn(() => of(acme)),
    delete: vi.fn(() => of(undefined)),
  };
  let page: EntreprisesComponent;

  beforeEach(async () => {
    vi.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [EntreprisesComponent],
      providers: [{ provide: EntrepriseService, useValue: service }],
    }).compileComponents();
    const fixture = TestBed.createComponent(EntreprisesComponent);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads the companies on init and renders them', () => {
    expect(service.getAll).toHaveBeenCalledTimes(1);
    expect(page.entreprises()).toEqual([acme]);
  });

  it('adds a new company, then reloads and closes the form', () => {
    page.openAdd();
    page.update('nom', 'Globex');
    page.update('adresse', 'Sfax');
    page.save();
    expect(service.add).toHaveBeenCalledWith({ nom: 'Globex', adresse: 'Sfax' });
    expect(service.getAll).toHaveBeenCalledTimes(2);
    expect(page.showForm()).toBe(false);
  });

  it('edits a copy and saves it with update', () => {
    page.edit(acme);
    page.update('adresse', 'Sousse');
    expect(acme.adresse).toBe('Tunis');
    page.save();
    expect(service.update).toHaveBeenCalledWith({ ...acme, adresse: 'Sousse' });
  });

  it('deletes only after confirmation', () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true);
    page.delete(1);
    expect(service.delete).not.toHaveBeenCalled();
    page.delete(1);
    expect(service.delete).toHaveBeenCalledWith(1);
    confirm.mockRestore();
  });
});
