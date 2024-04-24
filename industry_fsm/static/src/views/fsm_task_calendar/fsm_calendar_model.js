/** @odoo-module */

import { ProjectTaskCalendarModel } from '@project/views/project_task_calendar/project_task_calendar_model';

export class FsmTaskCalendarModel extends ProjectTaskCalendarModel {
    makeContextDefaults(record) {
        return super.makeContextDefaults(record);
    }
}
