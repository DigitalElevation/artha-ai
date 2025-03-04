import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load = (async ({ parent }) => {
	const { user } = await parent();

	// Verificar se o usuário está logado e tem permissão de administrador
	if (!user || user.role !== 'admin') {
		throw redirect(302, '/');
	}

	return {};
}) satisfies PageLoad; 