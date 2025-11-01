import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NotificationsService, AlertItem } from '../../services/notifications.service';

@Component({
    selector: 'app-alerts-inbox',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './alerts-inbox.component.html',
    styleUrls: ['./alerts-inbox.component.scss']
})
export class AlertsInboxComponent implements OnInit {
    alerts: AlertItem[] = [];
    onlyUnread = signal<boolean>(false);
    unreadCount = 0;
    loading = false;

    constructor(private notifications: NotificationsService) { }

    ngOnInit(): void {
        this.notifications.alertsStream.subscribe(a => this.alerts = a);
        this.notifications.unreadCountStream.subscribe(c => this.unreadCount = c);
        this.reload();
    }

    reload() {
        this.loading = true;
        this.notifications.fetch(this.onlyUnread()).subscribe({
            next: () => (this.loading = false),
            error: () => (this.loading = false)
        });
    }

    toggleUnread() {
        this.onlyUnread.set(!this.onlyUnread());
        this.reload();
    }

    markRead(a: AlertItem) {
        if (a.read_at) return;
        this.notifications.markRead(a.id).subscribe();
    }

    markAll() {
        if (this.unreadCount === 0) return;
        this.notifications.markAllRead().subscribe();
    }

    iconFor(type: string): string {
        switch (type) {
            case 'NEW_PQRS': return '📬';
            case 'PQRS_ASSIGNED': return '📌';
            default: return '🔔';
        }
    }
}
