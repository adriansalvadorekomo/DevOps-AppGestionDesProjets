import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { ProjetsComponent } from './projets';
import { ProjetService } from '../../services/projet.service';

describe('ProjetsComponent', () => {
  const erp = { id: 2, sujet: 'ERP' };
  const service = {
    getAll: vi.fn(() => of([erp])),
    add: vi.fn(() => of(erp)),
    update: vi.fn(() => of(erp)),
    delete: vi.fn(() => of(undefined)),
  };
  let page: ProjetsComponent;

  beforeEach(async () => {
    vi.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [ProjetsComponent],
      providers: [{ provide: ProjetService, useValue: service }],
    }).compileComponents();
    const fixture = TestBed.createComponent(ProjetsComponent);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads the projects on init', () => {
    expect(page.projets()).toEqual([erp]);
  });

  it('adds, edits and deletes through the service', () => {
    page.openAdd();
    page.update('sujet', 'CRM');
    page.save();
    expect(service.add).toHaveBeenCalledWith({ sujet: 'CRM' });

    page.edit(erp);
    page.save();
    expect(service.update).toHaveBeenCalledWith(erp);
    expect(page.showForm()).toBe(false);

    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);
    page.delete(2);
    expect(service.delete).toHaveBeenCalledWith(2);
    expect(service.getAll).toHaveBeenCalledTimes(4);
    confirm.mockRestore();
  });
});
