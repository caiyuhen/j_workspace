<<<<<<< HEAD
import bcrypt from 'bcryptjs';
=======
import bcrypt from 'bcrypt';
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8

const SALT_ROUNDS = 12;

/**
 * 哈希密码
 */
export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

/**
 * 验证密码
 */
export async function comparePassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
