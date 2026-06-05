
import { MATRIX_DATA } from './data-loader';
export { MATRIX_DATA } from './data-loader';
export * from './types';

export const getTasks = (roleId?: string, stageId?: string) => {
  return MATRIX_DATA.filter(d => 
    (!roleId || d.roleId === roleId) && 
    (!stageId || d.stageId === stageId)
  );
};
