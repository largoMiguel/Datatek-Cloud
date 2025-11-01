import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationsService, AlertItem } from '../../../services/notifications.service';
import { Subscription } from 'rxjs';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './topbar.component.html',
    styleUrls: ['./topbar.component.scss']
})
export class TopbarComponent implements OnInit, OnDestroy {
    isOpen = false;
    alerts: AlertItem[] = [];
    unreadCount = 0;
    private sub?: Subscription;
    private sub2?: Subscription;

    constructor(private notifications: NotificationsService) { }

    ngOnInit(): void {
        this.sub = this.notifications.alertsStream.subscribe(a => this.alerts = a);
        this.sub2 = this.notifications.unreadCountStream.subscribe(c => this.unreadCount = c);
        // Primer fetch para tener contador
        this.notifications.fetch(true).subscribe();
    }

    ngOnDestroy(): void {
        this.sub?.unsubscribe();
        this.sub2?.unsubscribe();
    }

    togglePanel() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.notifications.fetch(false).subscribe();
        }
    }

    markRead(a: AlertItem, event?: MouseEvent) {
        event?.stopPropagation();
        if (a.read_at) return;
        this.notifications.markRead(a.id).subscribe();
    }

    markAll(event?: MouseEvent) {
        event?.stopPropagation();
        if (this.unreadCount === 0) return;
        this.notifications.markAllRead().subscribe();
    }

    refresh(event?: MouseEvent) {
        event?.stopPropagation();
        this.notifications.fetch(false).subscribe();
    }

    @HostListener('document:click', ['$event'])
    onDocumentClick(event: MouseEvent) {
        const target = event.target as HTMLElement;
        // Cerrar si se hace clic fuera del panel o del botón
        if (!target.closest('.topbar__bell') && !target.closest('.alerts-panel')) {
            this.isOpen = false;
        }
    }
}
